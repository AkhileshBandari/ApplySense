from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from profiles.models import Profile, Skill, VerificationStatus
from .models import CareerPath, CareerPathScenario, ScenarioAssumption, AssumptionType, ScenarioStatus
from .services import CareerPathRecommendationService, ScenarioSimulationEngine
import json

User = get_user_model()

class CareerPathwaysTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='user1', email='user1@test.com', password='password123')
        self.user2 = User.objects.create_user(username='user2', email='user2@test.com', password='password123')
        
        self.profile1 = Profile.objects.create(user=self.user1, name="User One")
        Skill.objects.create(profile=self.profile1, name="Python", verification_status=VerificationStatus.VERIFIED)
        Skill.objects.create(profile=self.profile1, name="Django", verification_status=VerificationStatus.VERIFIED)
        
        self.path_backend = CareerPath.objects.create(
            canonical_role_name="Backend Developer",
            target_role="Backend Developer",
            active=True
        )
        self.path_backend.requirements.create(canonical_skill="Python")
        self.path_backend.requirements.create(canonical_skill="Django")
        self.path_backend.requirements.create(canonical_skill="Docker")
        
        self.client.force_authenticate(user=self.user1)

    def test_recommendation_deterministic_scoring(self):
        """Ensure the readiness score is deterministically calculated without LLM."""
        recs = CareerPathRecommendationService.evaluate_paths_for_user(self.user1)
        self.assertEqual(len(recs), 1)
        
        backend_rec = recs[0]
        self.assertEqual(backend_rec['role_name'], "Backend Developer")
        
        # User has 2 out of 3 skills -> 66% coverage -> 66 skill score
        # 66 * 0.7 + 0 * 0.3 = 46 overall readiness
        self.assertEqual(backend_rec['skill_score'], 66)
        self.assertEqual(backend_rec['overall_readiness'], 39)
        self.assertEqual(backend_rec['classification'], "SIGNIFICANT_GAP")

    def test_scenario_baseline_immutability(self):
        """Ensure scenario baseline snapshot does not change when CandidateContext changes later."""
        scenario = ScenarioSimulationEngine.create_scenario(self.user1, "My Scenario", self.path_backend.id)
        
        # Snapshot has Python and Django
        baseline_skills = [s['name'] for s in scenario.baseline_snapshot.get('skills', [])]
        self.assertIn("Python", baseline_skills)
        self.assertNotIn("Docker", baseline_skills)
        
        # Later, user verifies Docker in reality
        Skill.objects.create(profile=self.profile1, name="Docker", verification_status=VerificationStatus.VERIFIED)
        
        # Scenario baseline should still NOT have Docker
        scenario.refresh_from_db()
        baseline_skills_after = [s['name'] for s in scenario.baseline_snapshot.get('skills', [])]
        self.assertNotIn("Docker", baseline_skills_after)
        
    def test_scenario_simulation_delta(self):
        """Ensure assuming a skill works in simulation but doesn't mutate candidate."""
        scenario = ScenarioSimulationEngine.create_scenario(self.user1, "Learn Docker", self.path_backend.id)
        ScenarioAssumption.objects.create(
            scenario=scenario,
            assumption_type=AssumptionType.SKILL,
            structured_data={"skill": "Docker"}
        )
        
        delta = ScenarioSimulationEngine.simulate(scenario)
        self.assertEqual(scenario.status, ScenarioStatus.SIMULATED)
        
        # Simulated state has Docker
        sim_skills = [s['name'] for s in scenario.simulated_snapshot.get('skills', [])]
        self.assertIn("Docker", sim_skills)
        self.assertIn("Docker", delta['acquired_skills'])
        
        # Real candidate context still doesn't have Docker
        real_skills = Skill.objects.filter(profile=self.profile1, name="Docker").count()
        self.assertEqual(real_skills, 0)
        
    def test_cross_user_isolation(self):
        """Ensure user2 cannot view or mutate user1's scenarios."""
        scenario = ScenarioSimulationEngine.create_scenario(self.user1, "User1 Scenario")
        
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(f'/api/career-pathways/scenarios/{scenario.id}/')
        self.assertEqual(response.status_code, 404)
        
    def test_create_scenario_api(self):
        """Ensure API creates scenario with assumptions properly."""
        payload = {
            "name": "Target AI",
            "target_role": "AI Engineer",
            "assumptions": [
                {
                    "assumption_type": "SKILL",
                    "structured_data": {"skill": "PyTorch"}
                }
            ]
        }
        response = self.client.post('/api/career-pathways/scenarios/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], "Target AI")
        self.assertEqual(len(response.data['assumptions']), 1)
        
        # Now simulate
        sim_response = self.client.post(f"/api/career-pathways/scenarios/{response.data['id']}/simulate/")
        self.assertEqual(sim_response.status_code, 200)
        self.assertIn("PyTorch", sim_response.data['delta']['acquired_skills'])
