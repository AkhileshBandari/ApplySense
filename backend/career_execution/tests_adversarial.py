from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from career_decisions.models import CareerDecisionPlanVersion, CareerAction, CareerActionDependency
from career_execution.models import CareerExecutionPlan, CareerExecutionItem, CareerExecutionDependency, ExecutionStatus, ExecutionMode, CareerExecutionProgress
from career_execution.services.reconciliation_service import ActionReconciliationService
from career_execution.services.safety_boundary import ExecutionEligibilityService

User = get_user_model()

class CareerExecutionAdversarialTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="usera", email="a@example.com", password="password")
        self.user_b = User.objects.create_user(username="userb", email="b@example.com", password="password")
        
        self.client_a = APIClient()
        self.client_a.force_authenticate(user=self.user_a)
        
        self.client_b = APIClient()
        self.client_b.force_authenticate(user=self.user_b)
        
        self.unauth_client = APIClient()
        
        # Create baseline decision plan for User A
        self.plan_a = CareerDecisionPlanVersion.objects.create(user=self.user_a, is_active=True)
        self.action_a1 = CareerAction.objects.create(
            plan_version=self.plan_a, title="A1", action_type="USER_ACTION", source_phase="LEARNING", final_score=90
        )
        self.action_a2 = CareerAction.objects.create(
            plan_version=self.plan_a, title="A2", action_type="AUTO_EXECUTABLE", source_phase="APPLICATION", final_score=100
        )
        CareerActionDependency.objects.create(action=self.action_a2, depends_on=self.action_a1)
        
        ActionReconciliationService.reconcile_plan(self.user_a)
        self.exec_plan_a = CareerExecutionPlan.objects.get(user=self.user_a)

    def test_authentication_attacks(self):
        # 401 Unauthenticated
        response = self.unauth_client.get('/api/career-execution/current/')
        self.assertEqual(response.status_code, 401)
        
        response = self.unauth_client.get('/api/career-execution/progress/')
        self.assertEqual(response.status_code, 401)

    def test_cross_user_attacks(self):
        # User B attempts to access User A's execution items
        item_a1 = self.exec_plan_a.items.get(title="A1")
        response = self.client_b.post(f'/api/career-execution/items/{item_a1.id}/complete/')
        self.assertEqual(response.status_code, 404)

    def test_completion_bypass_and_client_authority(self):
        # Client tries to inject status in a complete call
        item_a1 = self.exec_plan_a.items.get(title="A1")
        response = self.client_a.post(f'/api/career-execution/items/{item_a1.id}/complete/', {"status": "COMPLETED", "execution_mode": "AUTO_EXECUTABLE"})
        self.assertEqual(response.status_code, 200)
        
        # Verify it did complete
        item_a1.refresh_from_db()
        self.assertEqual(item_a1.status, ExecutionStatus.COMPLETED)
        self.assertNotEqual(item_a1.execution_mode, ExecutionMode.AUTO_EXECUTABLE)

    def test_dependency_attacks(self):
        # Action 2 depends on Action 1
        # Rebuild fresh to ensure action 1 is pending
        self.action_a1.status = "PENDING"
        self.action_a1.save()
        ActionReconciliationService.reconcile_plan(self.user_a)
        
        item_a1 = self.exec_plan_a.items.get(title="A1")
        item_a2 = self.exec_plan_a.items.get(title="A2")
        item_a1.status = ExecutionStatus.PENDING
        item_a1.save()
        item_a2.status = ExecutionStatus.BLOCKED
        item_a2.save()
        
        # Attempt to complete A2 while A1 is incomplete
        response = self.client_a.post(f'/api/career-execution/items/{item_a2.id}/complete/')
        self.assertEqual(response.status_code, 400)
        self.assertIn("Prerequisites are not met", str(response.data))

    def test_duplicate_action_attack(self):
        # Run reconciliation again
        ActionReconciliationService.reconcile_plan(self.user_a)
        self.assertEqual(self.exec_plan_a.items.count(), 2)

    def test_progress_manipulation(self):
        # Create a progress record manually
        CareerExecutionProgress.objects.create(user=self.user_a, overall_score=0)
        
        # Attempt to GET and inject data
        response = self.client_a.get('/api/career-execution/progress/')
        self.assertEqual(response.status_code, 200)
        # Assuming only GET is allowed on progress endpoint (we only implemented GET in viewset)
        # Any POST/PUT would be 405
        response = self.client_a.post('/api/career-execution/progress/', {"overall_score": 100})
        self.assertEqual(response.status_code, 405)

    def test_auto_apply_security_attack(self):
        # Action 2 is AUTO_EXECUTABLE, but since no Phase 5 safety passes, it should be downgraded to REVIEW_REQUIRED
        ActionReconciliationService.reconcile_plan(self.user_a)
        item_a2 = self.exec_plan_a.items.get(title="A2")
        # Item 2 is BLOCKED due to A1. Complete A1 to unblock it.
        item_a1 = self.exec_plan_a.items.get(title="A1")
        item_a1.status = ExecutionStatus.COMPLETED
        item_a1.save()
        ExecutionEligibilityService.update_item_mode(item_a2, self.user_a)
        item_a2.refresh_from_db()
        # Should be downgraded to REVIEW_REQUIRED because we didn't pass real AutoApply auth
        self.assertEqual(item_a2.execution_mode, ExecutionMode.REVIEW_REQUIRED)

    def test_stale_plan_detection_and_reconciliation(self):
        item_a1 = self.exec_plan_a.items.get(title="A1")
        
        # Remove A1 from decision plan
        self.action_a1.delete()
        
        ActionReconciliationService.reconcile_plan(self.user_a)
        item_a1.refresh_from_db()
        self.assertEqual(item_a1.status, ExecutionStatus.SUPERSEDED)

