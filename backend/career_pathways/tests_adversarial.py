from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from profiles.models import Profile, Skill, VerificationStatus
from career_pathways.models import CareerPath, CareerPathScenario, ScenarioAssumption, AssumptionType
from career_pathways.services import CareerPathRecommendationService, ScenarioSimulationEngine
# Need to mock or implement market demand and career brand for full verification
# We'll just test the logic

User = get_user_model()

class Phase7FAdversarialVerification(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='adv_user1', email='adv1@test.com', password='password123')
        self.user2 = User.objects.create_user(username='adv_user2', email='adv2@test.com', password='password123')
        
        self.profile1 = Profile.objects.create(user=self.user1, name="Adv User One")
        Skill.objects.create(profile=self.profile1, name="Python", verification_status=VerificationStatus.VERIFIED)
        
        self.path1 = CareerPath.objects.create(
            canonical_role_name="Backend",
            target_role="Backend",
            active=True
        )
        self.path1.requirements.create(canonical_skill="Python")
        self.path1.requirements.create(canonical_skill="Go")
        
        self.client.force_authenticate(user=self.user1)

    def test_A1_unauthenticated(self):
        self.client.logout()
        resp = self.client.get('/api/career-pathways/paths/')
        self.assertEqual(resp.status_code, 401)
        
    def test_A2_cross_user_isolation(self):
        scenario = ScenarioSimulationEngine.create_scenario(self.user1, "U1 Scenario", self.path1.id)
        self.client.force_authenticate(user=self.user2)
        resp = self.client.get(f'/api/career-pathways/scenarios/{scenario.id}/')
        self.assertEqual(resp.status_code, 404)
        
    def test_client_authority_attack(self):
        # Trying to inject readiness_score and verified=true
        payload = {
            "name": "Hacked",
            "readiness_score": 100,
            "status": "SIMULATED",
            "verified": True,
            "baseline_snapshot": {"hacked": True}
        }
        resp = self.client.post('/api/career-pathways/scenarios/', payload, format='json')
        self.assertEqual(resp.status_code, 201)
        
        # Check that server ignored it
        scenario = CareerPathScenario.objects.get(id=resp.data['id'])
        self.assertNotEqual(scenario.status, "SIMULATED")
        self.assertNotIn("hacked", scenario.baseline_snapshot)
        
    def test_candidate_context_trust_boundary(self):
        scenario = ScenarioSimulationEngine.create_scenario(self.user1, "Trust", self.path1.id)
        ScenarioAssumption.objects.create(
            scenario=scenario,
            assumption_type=AssumptionType.SKILL,
            structured_data={"skill": "Go"}
        )
        ScenarioSimulationEngine.simulate(scenario)
        
        # simulated state has Go
        sim_skills = [s['name'] for s in scenario.simulated_snapshot['skills']]
        self.assertIn("Go", sim_skills)
        
        # Real candidate context must not have Go
        real_go = Skill.objects.filter(profile=self.profile1, name="Go").exists()
        self.assertFalse(real_go, "Candidate context leaked from scenario!")
        
    def test_direct_verification_attack(self):
        scenario = ScenarioSimulationEngine.create_scenario(self.user1, "Verify", self.path1.id)
        ScenarioAssumption.objects.create(
            scenario=scenario,
            assumption_type=AssumptionType.SKILL,
            structured_data={"skill": "Go", "verification_status": "VERIFIED"}
        )
        ScenarioSimulationEngine.simulate(scenario)
        
        sim_skills = scenario.simulated_snapshot['skills']
        go_skill = next((s for s in sim_skills if s['name'] == 'Go'), None)
        self.assertTrue(go_skill['is_simulated']) # Must be simulated
        
    def test_numerical_determinism(self):
        recs = CareerPathRecommendationService.evaluate_paths_for_user(self.user1)
        rec = recs[0]
        self.assertTrue(0 <= rec['overall_readiness'] <= 100)
        self.assertEqual(rec['skill_score'], 50) # 1 of 2 skills
        
        # Ensure formula is calculated correctly without LLM randomness
        self.assertIn('market_alignment', rec)
        
    def test_market_placeholder_attack(self):
        # We need to verify that "Strong" is not hardcoded.
        # Initially, the code HAS "Strong" hardcoded.
        recs = CareerPathRecommendationService.evaluate_paths_for_user(self.user1)
        self.assertNotEqual(
            recs[0]['market_alignment'], 
            "Strong", 
            "Market demand is hardcoded! Must integrate Phase 7B."
        )

    def test_career_brand_integration(self):
        # Ensure that Career Brand is included in the readiness score instead of just 70/30 skill/interview.
        recs = CareerPathRecommendationService.evaluate_paths_for_user(self.user1)
        self.assertIn('brand_score', recs[0], "Missing Career Brand dimension in scoring.")
        
    def test_evidence_integration(self):
        recs = CareerPathRecommendationService.evaluate_paths_for_user(self.user1)
        self.assertIn('evidence_score', recs[0], "Missing Evidence dimension in scoring.")
