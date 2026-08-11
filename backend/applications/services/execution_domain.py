from django.utils import timezone
from applications.models import (
    Application, ApplicationExecution, SubmissionAttempt, SubmissionReceipt,
    ApplicationApproval, FormSession, ApplicationQuestion
)
from applications.constants import (
    ExecutionStatus, ExecutionMode, ReceiptSource, ExecutionError
)
from django.db import transaction
from django.core.exceptions import ValidationError

class PreExecutionValidationService:
    @staticmethod
    def validate_for_execution(user, application, snapshot_fingerprint):
        """
        Validates all prerequisites before allowing execution to proceed.
        Returns (is_valid, blocker_reason, execution_error_code).
        """
        if application.user != user:
            return False, "User does not own application", ExecutionError.POLICY_BLOCKED
        
        # 1. Approval Check
        approval = ApplicationApproval.objects.filter(
            application=application,
            approved_by=user,
            status='VALID'
        ).last()
        
        if not approval:
            return False, "No valid approval exists for this application", ExecutionError.POLICY_BLOCKED
            
        if approval.snapshot_fingerprint != snapshot_fingerprint:
            return False, "Approval is stale relative to current snapshot", ExecutionError.STALE_APPROVAL

        # 1.5 Provider Re-Detection and capability check
        from jobs.registries import ApplicationProviderRegistry, ImplementationStatus
        
        provider = application.application_provider
        if not provider:
            return False, "Application has no provider assigned", ExecutionError.POLICY_BLOCKED
            
        capability = ApplicationProviderRegistry.get_capability(provider)
        if capability.implementation_status in [ImplementationStatus.REGISTERED, ImplementationStatus.RESEARCHED, ImplementationStatus.DETECTION_ONLY, ImplementationStatus.BLOCKED]:
            return False, f"Provider {provider} is not implemented or blocked for execution", ExecutionError.POLICY_BLOCKED
            
        # Re-detection: compare active form session
        latest_session = application.form_sessions.order_by('-started_at').first()
        if latest_session and latest_session.provider != provider:
            return False, f"Re-detection mismatch: app provider {provider} vs session {latest_session.provider}", ExecutionError.POLICY_BLOCKED

        # 2. Global Pause & Policy checks
        policy = user.automation_policy
        if policy.global_pause:
            return False, "Automation globally paused", ExecutionError.GLOBAL_PAUSE

        # 3. Readiness check
        if application.status not in ['READY_TO_SUBMIT', 'REVIEW_REQUIRED', 'DRAFT', 'PREPARING']:
            return False, f"Application not in executable state: {application.status}", ExecutionError.POLICY_BLOCKED

        # 4. CAPTCHA / Consent blockers
        # We check questions for unanswered REQUIRED questions or SECRET fields mapped poorly
        unanswered_required = application.questions.filter(required=True, answer__isnull=True)
        if unanswered_required.exists():
            return False, "Unanswered required fields exist", ExecutionError.MISSING_REQUIRED_FIELD
            
        return True, None, None

class ExecutionRouter:
    @staticmethod
    def route_execution(application, provider_capability):
        """
        Calculates effective capability and maps to ExecutionMode.
        MIN(provider_capability, applysense_capability, policy_permission)
        """
        policy = application.user.automation_policy
        allowed_modes = policy.allowed_application_modes
        
        # This simplifies the complex MIN matrix down to deterministic fallbacks
        if provider_capability == 'AUTHORIZED_API_APPLY' and ExecutionMode.AUTHORIZED_API_SUBMISSION in allowed_modes:
            return ExecutionMode.AUTHORIZED_API_SUBMISSION
            
        if provider_capability == 'BROWSER_APPLY' and ExecutionMode.USER_CONFIRMED_BROWSER_SUBMISSION in allowed_modes:
            return ExecutionMode.USER_CONFIRMED_BROWSER_SUBMISSION
            
        if provider_capability in ['BROWSER_APPLY', 'ASSISTED_APPLY'] and ExecutionMode.ASSISTED_USER_SUBMISSION in allowed_modes:
            return ExecutionMode.ASSISTED_USER_SUBMISSION
            
        return ExecutionMode.MANUAL_HANDOFF

class ServerExecutionCapabilityResolver:
    @staticmethod
    def resolve(application, provider, source, provider_capability, policy, authorization_state):
        """
        Determines the execution mode for an auto-apply orchestration run.
        """
        from jobs.registries import ImplementationStatus
        
        if not provider_capability or provider_capability.implementation_status == ImplementationStatus.BLOCKED:
            return 'BLOCKED', 'Provider blocked globally'
            
        if source == 'LinkedIn' and not provider:
            return 'USER_ACTION_REQUIRED', 'LinkedIn hosted server execution not authorized'
            
        if source == 'Indeed' and not provider:
            if authorization_state != 'AUTHORIZED':
                return 'USER_ACTION_REQUIRED', 'Indeed partner API not authorized'
            return 'AUTHORIZED_API', 'Indeed Partner Apply authorized'
            
        if source == 'Naukri' and not provider:
            return 'USER_ACTION_REQUIRED', 'Naukri hosted server execution not authorized'
            
        if not provider_capability.server_execution_allowed:
            return 'USER_ACTION_REQUIRED', 'Server execution explicitly disabled for this provider'
            
        return 'SERVER_BROWSER', 'Server browser execution permitted'

class ExecutionReservationService:
    @staticmethod
    @transaction.atomic
    def reserve_execution_slot(user, application, idempotency_key=None):
        """
        Atomically checks limits and creates an execution to prevent double-click / concurrency bugs.
        """
        # Lock the policy to prevent concurrent daily limit races
        from applications.models import AutomationPolicy
        policy = AutomationPolicy.objects.select_for_update().get(user=user)
        
        # Daily limit logic conceptually (assume we check attempts today)
        today = timezone.now().date()
        daily_attempts = ApplicationExecution.objects.filter(
            user=user, 
            created_at__date=today
        ).count()
        
        from automation.models import AutoApplyConfiguration
        config = AutoApplyConfiguration.objects.filter(user=user).first()
        limit = config.daily_application_limit if config and config.daily_application_limit else policy.daily_application_limit
        
        if daily_attempts >= limit:
            return False, None, ExecutionError.DAILY_LIMIT_REACHED

        # Check for active execution on this app (atomically locked via policy)
        active_execs = ApplicationExecution.objects.filter(
            application=application,
            execution_status__in=[ExecutionStatus.CREATED, ExecutionStatus.VALIDATING, ExecutionStatus.READY, ExecutionStatus.EXECUTING, ExecutionStatus.VERIFYING]
        )
        if active_execs.exists():
            return False, None, ExecutionError.EXECUTION_ALREADY_ACTIVE
            
        execution = ApplicationExecution.objects.create(
            user=user,
            application=application,
            snapshot_fingerprint=application.snapshot.get('fingerprint') if application.snapshot else 'unknown',
            idempotency_key=idempotency_key,
            execution_status=ExecutionStatus.CREATED
        )
        return True, execution, None

class ApplicationExecutionStateMachine:
    VALID_TRANSITIONS = {
        ExecutionStatus.CREATED: [ExecutionStatus.VALIDATING],
        ExecutionStatus.VALIDATING: [ExecutionStatus.BLOCKED, ExecutionStatus.AWAITING_USER, ExecutionStatus.READY],
        ExecutionStatus.READY: [ExecutionStatus.EXECUTING, ExecutionStatus.CANCELLED],
        ExecutionStatus.EXECUTING: [ExecutionStatus.VERIFYING, ExecutionStatus.FAILED, ExecutionStatus.UNKNOWN_RESULT],
        ExecutionStatus.VERIFYING: [ExecutionStatus.SUCCEEDED, ExecutionStatus.FAILED, ExecutionStatus.UNKNOWN_RESULT],
        ExecutionStatus.UNKNOWN_RESULT: [ExecutionStatus.SUCCEEDED, ExecutionStatus.FAILED],
    }

    @staticmethod
    def transition(execution, new_status, failure_reason=None):
        if new_status not in ApplicationExecutionStateMachine.VALID_TRANSITIONS.get(execution.execution_status, []):
            raise ValidationError(f"Invalid execution transition from {execution.execution_status} to {new_status}")
            
        execution.execution_status = new_status
        if new_status == ExecutionStatus.VALIDATING:
            execution.started_at = timezone.now()
        elif new_status in [ExecutionStatus.SUCCEEDED, ExecutionStatus.FAILED, ExecutionStatus.UNKNOWN_RESULT, ExecutionStatus.BLOCKED, ExecutionStatus.CANCELLED]:
            execution.completed_at = timezone.now()
            
        if failure_reason:
            execution.failure_reason = failure_reason
            
        execution.save()
        return execution

class SubmissionVerificationService:
    @staticmethod
    def verify_receipt(execution, provider, evidence):
        """
        Inspects provider-specific evidence (e.g. success URLs, text) to issue receipt.
        """
        # Mock logic based on provider evidence
        if evidence.get('success_marker'):
            receipt = SubmissionReceipt.objects.create(
                application=execution.application,
                execution=execution,
                provider=provider,
                receipt_source=ReceiptSource.CONFIRMATION_PAGE,
                execution_mode=execution.application_mode,
                submitted_at=timezone.now()
            )
            # Sync application status
            execution.application.status = 'SUBMITTED'
            execution.application.submitted_at = timezone.now()
            execution.application.save()
            return receipt
            
        return None

class ReconciliationService:
    @staticmethod
    def reconcile_unknown(execution, user_confirmed=False):
        """
        Allows a user to manually resolve an UNKNOWN_RESULT to SUCCEEDED or FAILED.
        """
        if execution.execution_status != ExecutionStatus.UNKNOWN_RESULT:
            return False, "Only UNKNOWN_RESULT executions can be reconciled."
            
        if user_confirmed:
            receipt = SubmissionReceipt.objects.create(
                application=execution.application,
                execution=execution,
                provider=execution.provider,
                receipt_source=ReceiptSource.USER_CONFIRMED,
                execution_mode=execution.application_mode,
                submitted_at=timezone.now()
            )
            ApplicationExecutionStateMachine.transition(execution, ExecutionStatus.SUCCEEDED)
            execution.application.status = 'SUBMITTED'
            execution.application.submitted_at = timezone.now()
            execution.application.save()
            return True, receipt
            
        # Reconciled as failed
        ApplicationExecutionStateMachine.transition(execution, ExecutionStatus.FAILED, "User marked as failed.")
        execution.application.status = 'APPLICATION_FAILED'
        execution.application.save()
        return True, None
