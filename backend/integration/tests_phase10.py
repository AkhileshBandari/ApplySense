from django.test import TestCase
from django.contrib.auth import get_user_model
from career_integration.models import (
    CareerOperatingState, UserActionItem, SystemState, SystemBlocker, DomainName
)
from career_integration.services.os_orchestrator import OSOrchestratorService
from profiles.models import Profile
from evidence.models import GitHubConnection
from automation.models import AutoApplyRun

User = get_user_model()

class Phase10IntegrationTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(username='os_test', email='os@test.com', password='password123')
        
    def test_end_to_end_readiness(self):
        # 1. Onboarding
        state = OSOrchestratorService.evaluate_os_readiness(self.user)
        self.assertEqual(state.current_os_state, SystemState.ONBOARDING)
        
        # We expect action items for Missing Context and Missing Evidence
        actions = UserActionItem.objects.filter(user=self.user, is_resolved=False)
        self.assertTrue(actions.filter(blocker_type=SystemBlocker.MISSING_VERIFIED_SKILL).exists())
        self.assertTrue(actions.filter(blocker_type=SystemBlocker.MISSING_EVIDENCE).exists())
        
        # 2. Add Context
        Profile.objects.create(user=self.user, name="Test")
        state = OSOrchestratorService.evaluate_os_readiness(self.user)
        
        # Next state should be PROFILE_READY because we don't have ProfessionalProfile
        self.assertEqual(state.current_os_state, SystemState.PROFILE_READY)
        
        # The MISSING_VERIFIED_SKILL action should be resolved
        actions = UserActionItem.objects.filter(user=self.user, is_resolved=False)
        self.assertFalse(actions.filter(blocker_type=SystemBlocker.MISSING_VERIFIED_SKILL).exists())
        
        # 3. Add Evidence
        GitHubConnection.objects.create(user=self.user, github_username="testgit")
        OSOrchestratorService.evaluate_os_readiness(self.user)
        
        actions = UserActionItem.objects.filter(user=self.user, is_resolved=False)
        self.assertFalse(actions.filter(blocker_type=SystemBlocker.MISSING_EVIDENCE).exists())
        
    def test_auto_apply_blocker_propagation(self):
        # Create an auto-apply run that requires user action
        run = AutoApplyRun.objects.create(
            user=self.user,
            status='COMPLETED',
            applications_user_action_required=1
        )
        OSOrchestratorService.evaluate_os_readiness(self.user)
        
        # Action Center should have an actionable item
        action = UserActionItem.objects.get(
            user=self.user,
            blocker_type=SystemBlocker.USER_ACTION_REQUIRED,
            is_resolved=False
        )
        self.assertEqual(action.source_domain, DomainName.EXECUTION)
        self.assertEqual(action.context_data.get('run_id'), run.id)
        
        # If run succeeds, it should resolve
        run.applications_user_action_required = 0
        run.save()
        
        OSOrchestratorService.evaluate_os_readiness(self.user)
        self.assertTrue(UserActionItem.objects.get(id=action.id).is_resolved)
