from django.test import TestCase
from django.contrib.auth import get_user_model
from applications.models import (
    Application, ApplicationExecution, SubmissionAttempt, SubmissionReceipt,
    ApplicationApproval, AutomationPolicy, ApplicationQuestion
)
from applications.constants import ExecutionStatus, ExecutionMode, ReceiptSource, ExecutionError
from applications.services.execution_domain import (
    PreExecutionValidationService, ExecutionRouter, ExecutionReservationService,
    ApplicationExecutionStateMachine, ReconciliationService
)
from django.utils import timezone

User = get_user_model()

class Phase5DExecutionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@applysense.ai', password='password')
        self.policy = AutomationPolicy.objects.create(
            user=self.user, 
            automation_enabled=True,
            daily_application_limit=2,
            allowed_application_modes=[
                ExecutionMode.USER_CONFIRMED_BROWSER_SUBMISSION,
                ExecutionMode.ASSISTED_USER_SUBMISSION
            ]
        )
        self.application = Application.objects.create(
            user=self.user,
            role='Software Engineer',
            application_provider='Greenhouse',
            status='READY_TO_SUBMIT',
            snapshot={'fingerprint': 'safe_hash_123'}
        )
        
    def test_pre_execution_validation_success(self):
        ApplicationApproval.objects.create(
            application=self.application,
            approved_by=self.user,
            snapshot_fingerprint='safe_hash_123',
            status='VALID'
        )
        is_valid, blocker, err = PreExecutionValidationService.validate_for_execution(
            self.user, self.application, 'safe_hash_123'
        )
        self.assertTrue(is_valid)

    def test_stale_approval_blocked(self):
        ApplicationApproval.objects.create(
            application=self.application,
            approved_by=self.user,
            snapshot_fingerprint='old_hash_000',
            status='VALID'
        )
        is_valid, blocker, err = PreExecutionValidationService.validate_for_execution(
            self.user, self.application, 'new_hash_999'
        )
        self.assertFalse(is_valid)
        self.assertEqual(err, ExecutionError.STALE_APPROVAL)
        
    def test_missing_required_question_blocked(self):
        ApplicationApproval.objects.create(
            application=self.application,
            approved_by=self.user,
            snapshot_fingerprint='safe_hash_123',
            status='VALID'
        )
        # Create an unanswered required question
        ApplicationQuestion.objects.create(
            application=self.application,
            question_key='phone',
            required=True,
            answer=None
        )
        is_valid, blocker, err = PreExecutionValidationService.validate_for_execution(
            self.user, self.application, 'safe_hash_123'
        )
        self.assertFalse(is_valid)
        self.assertEqual(err, ExecutionError.MISSING_REQUIRED_FIELD)
        
    def test_global_pause_blocked(self):
        self.policy.global_pause = True
        self.policy.save()
        ApplicationApproval.objects.create(
            application=self.application,
            approved_by=self.user,
            snapshot_fingerprint='safe_hash_123',
            status='VALID'
        )
        is_valid, blocker, err = PreExecutionValidationService.validate_for_execution(
            self.user, self.application, 'safe_hash_123'
        )
        self.assertFalse(is_valid)
        self.assertEqual(err, ExecutionError.GLOBAL_PAUSE)
        
    def test_execution_router_capability_ceiling(self):
        # User allows browser submission, Provider allows browser submission
        mode = ExecutionRouter.route_execution(self.application, 'BROWSER_APPLY')
        self.assertEqual(mode, ExecutionMode.USER_CONFIRMED_BROWSER_SUBMISSION)
        
        # User allows browser, but Provider is DISCOVERY_ONLY
        mode2 = ExecutionRouter.route_execution(self.application, 'DISCOVERY_ONLY')
        self.assertEqual(mode2, ExecutionMode.MANUAL_HANDOFF)
        
    def test_execution_reservation_locks_duplicate(self):
        # First reservation
        success1, exec1, err1 = ExecutionReservationService.reserve_execution_slot(
            self.user, self.application, 'idem_123'
        )
        self.assertTrue(success1)
        
        # Concurrent / duplicate reservation attempt
        success2, exec2, err2 = ExecutionReservationService.reserve_execution_slot(
            self.user, self.application, 'idem_123'
        )
        self.assertFalse(success2)
        self.assertEqual(err2, ExecutionError.EXECUTION_ALREADY_ACTIVE)

    def test_daily_limit_atomicity(self):
        app2 = Application.objects.create(user=self.user, status='READY_TO_SUBMIT')
        app3 = Application.objects.create(user=self.user, status='READY_TO_SUBMIT')
        
        ExecutionReservationService.reserve_execution_slot(self.user, self.application)
        ExecutionReservationService.reserve_execution_slot(self.user, app2)
        
        # Limit is 2. The 3rd should fail.
        success, exec3, err = ExecutionReservationService.reserve_execution_slot(self.user, app3)
        self.assertFalse(success)
        self.assertEqual(err, ExecutionError.DAILY_LIMIT_REACHED)

    def test_cross_user_isolation(self):
        user2 = User.objects.create_user(username='hacker2', email='hacker@evil.com')
        AutomationPolicy.objects.create(user=user2)
        
        ApplicationApproval.objects.create(
            application=self.application,
            approved_by=self.user,
            snapshot_fingerprint='safe_hash_123',
            status='VALID'
        )
        
        is_valid, blocker, err = PreExecutionValidationService.validate_for_execution(
            user2, self.application, 'safe_hash_123'
        )
        self.assertFalse(is_valid)
        self.assertEqual(err, ExecutionError.POLICY_BLOCKED)

    def test_state_machine_invalid_transition(self):
        success, execution, err = ExecutionReservationService.reserve_execution_slot(self.user, self.application)
        
        # Valid
        ApplicationExecutionStateMachine.transition(execution, ExecutionStatus.VALIDATING)
        # Invalid jump to succeeded from validating
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            ApplicationExecutionStateMachine.transition(execution, ExecutionStatus.SUCCEEDED)

    def test_reconciliation_flow(self):
        success, execution, err = ExecutionReservationService.reserve_execution_slot(self.user, self.application)
        ApplicationExecutionStateMachine.transition(execution, ExecutionStatus.VALIDATING)
        ApplicationExecutionStateMachine.transition(execution, ExecutionStatus.READY)
        ApplicationExecutionStateMachine.transition(execution, ExecutionStatus.EXECUTING)
        ApplicationExecutionStateMachine.transition(execution, ExecutionStatus.UNKNOWN_RESULT)
        
        # Reconcile as succeeded by user
        success_rec, receipt = ReconciliationService.reconcile_unknown(execution, user_confirmed=True)
        self.assertTrue(success_rec)
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt.receipt_source, ReceiptSource.USER_CONFIRMED)
        
        execution.refresh_from_db()
        self.assertEqual(execution.execution_status, ExecutionStatus.SUCCEEDED)
        self.assertEqual(self.application.status, 'SUBMITTED')
