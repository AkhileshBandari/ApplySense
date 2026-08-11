
from django.test import TestCase
from django.contrib.auth import get_user_model
from career_decisions.models import CareerDecisionPlanVersion, CareerAction, CareerActionDependency
from career_execution.models import CareerExecutionPlan, CareerExecutionItem, ExecutionStatus, ExecutionMode
from career_execution.services.reconciliation_service import ActionReconciliationService
from career_execution.services.safety_boundary import ExecutionEligibilityService
from career_execution.services.execution_service import NextBestActionService, ExecutionLifecycleService

User = get_user_model()

class CareerExecutionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password")
        
        # Setup a Decision Plan
        self.decision_plan = CareerDecisionPlanVersion.objects.create(user=self.user, is_active=True)
        
        self.action1 = CareerAction.objects.create(
            plan_version=self.decision_plan, title="Action 1", action_type="USER_ACTION", source_phase="LEARNING",
            impact_score=50, final_score=50
        )
        self.action2 = CareerAction.objects.create(
            plan_version=self.decision_plan, title="Action 2", action_type="AUTO_EXECUTABLE", source_phase="APPLICATION",
            impact_score=80, final_score=80
        )
        
        # Action 2 depends on Action 1
        CareerActionDependency.objects.create(action=self.action2, depends_on=self.action1)

    def test_reconciliation_creates_execution_plan(self):
        exec_plan = ActionReconciliationService.reconcile_plan(self.user)
        self.assertIsNotNone(exec_plan)
        self.assertEqual(exec_plan.items.count(), 2)
        
        item1 = exec_plan.items.get(title="Action 1")
        item2 = exec_plan.items.get(title="Action 2")
        
        self.assertEqual(item2.dependencies.count(), 1)
        self.assertEqual(item2.dependencies.first().depends_on, item1)

    def test_eligibility_blocks_dependencies(self):
        ActionReconciliationService.reconcile_plan(self.user)
        
        plan = CareerExecutionPlan.objects.get(user=self.user)
        item1 = plan.items.get(title="Action 1")
        item2 = plan.items.get(title="Action 2")
        
        # Item 1 is USER_ACTION, no dependencies
        self.assertEqual(item1.execution_mode, ExecutionMode.USER_ACTION)
        
        # Item 2 is BLOCKED because it depends on Item 1 which is PENDING
        self.assertEqual(item2.status, ExecutionStatus.BLOCKED)
        self.assertEqual(item2.execution_mode, ExecutionMode.BLOCKED)

    def test_next_best_action_excludes_blocked(self):
        ActionReconciliationService.reconcile_plan(self.user)
        
        # Even though Action 2 has higher score (80), it is blocked. So Next Action should be Action 1 (50).
        next_action = NextBestActionService.get_next_action(self.user)
        self.assertEqual(next_action.title, "Action 1")

    def test_completing_action_unblocks_dependents(self):
        ActionReconciliationService.reconcile_plan(self.user)
        
        plan = CareerExecutionPlan.objects.get(user=self.user)
        item1 = plan.items.get(title="Action 1")
        item2 = plan.items.get(title="Action 2")
        
        ExecutionLifecycleService.complete_action(item1, self.user)
        
        # Reload item2
        item2.refresh_from_db()
        
        # Should now be READY (or auto-executable based on fallback safety boundary). 
        # Since it has no actual Phase 5 auth passing here, safety boundary will downgrade it to REVIEW_REQUIRED.
        self.assertNotEqual(item2.status, ExecutionStatus.BLOCKED)
        self.assertEqual(item2.execution_mode, ExecutionMode.REVIEW_REQUIRED)

    def test_reconciliation_supersedes_missing_actions(self):
        ActionReconciliationService.reconcile_plan(self.user)
        
        # Now remove Action 1 from Decision Plan
        self.action1.delete()
        
        ActionReconciliationService.reconcile_plan(self.user)
        
        plan = CareerExecutionPlan.objects.get(user=self.user)
        item1 = plan.items.get(title="Action 1")
        
        self.assertEqual(item1.status, ExecutionStatus.SUPERSEDED)
