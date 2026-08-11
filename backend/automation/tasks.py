import logging
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from automation.models import AutoApplyConfiguration, AutoApplyRun
from applications.models import ApplicationExecution, SubmissionReceipt
from applications.constants import ExecutionStatus

logger = logging.getLogger(__name__)

@shared_task
def schedule_auto_apply_runs():
    """
    Periodic task to find users who have auto apply enabled
    and trigger a run for them if appropriate.
    """
    configs = AutoApplyConfiguration.objects.filter(auto_apply_enabled=True)
    
    for config in configs:
        # Avoid concurrent runs for same user
        active_runs = AutoApplyRun.objects.filter(
            user=config.user, 
            status__in=['QUEUED', 'RUNNING']
        )
        if not active_runs.exists():
            run = AutoApplyRun.objects.create(
                user=config.user,
                status='QUEUED',
                trigger='SCHEDULED'
            )
            execute_auto_apply_run.delay(run.id)
            logger.info(f"Scheduled AutoApplyRun {run.id} for user {config.user_id}")

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def execute_auto_apply_run(self, run_id):
    """
    Primary worker task that orchestrates the entire application flow for a user.
    Hardened with transaction.atomic and select_for_update to prevent concurrency overlaps.
    """
    from automation.services.orchestrator import AutoApplyOrchestrator
    
    logger.info(f"Starting execution of AutoApplyRun {run_id}")
    
    try:
        with transaction.atomic():
            # Lock the run to prevent parallel worker execution
            try:
                run = AutoApplyRun.objects.select_for_update(nowait=True).get(id=run_id)
            except AutoApplyRun.DoesNotExist:
                logger.warning(f"AutoApplyRun {run_id} not found.")
                return
            except Exception as e:
                # If locked by another transaction, it will throw an exception (OperationalError).
                logger.warning(f"AutoApplyRun {run_id} is locked by another process.")
                raise e # Retry via autoretry_for
                
            # Check user config explicitly again at runtime
            config = AutoApplyConfiguration.objects.filter(user=run.user).first()
            if not config or not config.auto_apply_enabled:
                logger.info(f"AutoApply disabled for user {run.user_id}. Cancelling run {run_id}.")
                run.status = 'CANCELLED'
                run.save()
                return

            orchestrator = AutoApplyOrchestrator(run)
            orchestrator.execute()
            logger.info(f"Finished AutoApplyRun {run_id}")
            
    except Exception as e:
        logger.error(f"Error in execute_auto_apply_run {run_id}: {str(e)}")
        raise e

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def reconcile_unknown_submissions(self):
    """
    Finds executions stuck in UNKNOWN_RESULT or stuck in EXECUTING for too long,
    and tries to reconcile them by checking the ATS backend or timing them out.
    """
    timeout_threshold = timezone.now() - timezone.timedelta(minutes=30)
    
    with transaction.atomic():
        stuck_executions = ApplicationExecution.objects.select_for_update(skip_locked=True).filter(
            execution_status=ExecutionStatus.EXECUTING,
            started_at__lt=timeout_threshold
        )
        for execution in stuck_executions:
            logger.info(f"Timing out stuck execution {execution.id}")
            # Hard fail
            execution.execution_status = ExecutionStatus.FAILED
            execution.failure_reason = "Execution timed out without receipt"
            execution.completed_at = timezone.now()
            execution.save()
            
    # For Phase 5F, we just leave UNKNOWN_RESULT or let manual reconciliation happen via API.
    pass
