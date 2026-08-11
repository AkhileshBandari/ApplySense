import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from career_decisions.models import CareerDecisionPlanVersion, PriorityCategory, ActionType
from career_decisions.services.action_engine import ActionRankingService
from career_decisions.services.snapshot_service import CareerDecisionSnapshotService
from rest_framework.test import APIClient

User = get_user_model()

class CareerDecisionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="decisionuser", email="decision@example.com", password="password")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
    def test_deterministic_action_scoring(self):
        # score = impact + urgency + readiness - (effort * 0.5) - (deps_count * 10)
        score = ActionRankingService.calculate_score(
            impact=80, urgency=50, readiness=20, effort=60, deps_count=0
        )
        self.assertEqual(score, 100) # 80 + 50 + 20 - 30 - 0 = 120 -> max bounded to 100
        
        score2 = ActionRankingService.calculate_score(
            impact=10, urgency=10, readiness=10, effort=80, deps_count=2
        )
        self.assertEqual(score2, 0) # 30 - 40 - 20 = -30 -> min bounded to 0
        
    def test_snapshot_hashing_determinism(self):
        data1 = {"a": 1, "b": {"c": 2}}
        data2 = {"b": {"c": 2}, "a": 1}
        
        hash1 = CareerDecisionSnapshotService.hash_snapshot(data1)
        hash2 = CareerDecisionSnapshotService.hash_snapshot(data2)
        self.assertEqual(hash1, hash2, "Hashing must be deterministic despite dict order")
        
    def test_plan_generation_api(self):
        response = self.client.get('/api/career-decisions/current/')
        self.assertEqual(response.status_code, 200)
        
        # Verify it created a plan
        plan = CareerDecisionPlanVersion.objects.filter(user=self.user).first()
        self.assertIsNotNone(plan)
        
        # Calling again should not create a new plan (same hash)
        self.client.get('/api/career-decisions/current/')
        self.assertEqual(CareerDecisionPlanVersion.objects.count(), 1)
        
    def test_action_completion(self):
        response = self.client.get('/api/career-decisions/current/')
        plan = CareerDecisionPlanVersion.objects.filter(user=self.user).first()
        # Create dummy action
        action = plan.actions.create(title="Test", description="Test", action_type=ActionType.INFORMATIONAL)
        
        url = f'/api/career-decisions/actions/{action.id}/complete/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        
        action.refresh_from_db()
        self.assertEqual(action.status, 'COMPLETED')
