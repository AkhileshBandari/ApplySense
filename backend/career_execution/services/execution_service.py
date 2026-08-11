from career_execution.models import CareerExecutionPlan, CareerExecutionItem, ExecutionStatus, ExecutionMode, CareerExecutionOutcome, OutcomeType, CareerExecutionEvent
from career_execution.services.progress_engine import CareerProgressEngine
from career_execution.services.safety_boundary import ExecutionEligibilityService
from django.utils import timezone

class ExecutionLifecycleService:
    @staticmethod
    def complete_action(item: CareerExecutionItem, user, details=None):
        if item.status == ExecutionStatus.COMPLETED:
            return item
            
        # 1. Update state
        item.status = ExecutionStatus.COMPLETED
        item.completed_at = timezone.now()
        item.save()
        
        # 2. Record outcome
        CareerExecutionOutcome.objects.create(
            item=item,
            outcome_type=OutcomeType.SUCCESS,
            details=details or {}
        )
        
        # 3. Log event
        CareerExecutionEvent.objects.create(
            user=user,
            event_type="ACTION_COMPLETED",
            item=item,
            details={"title": item.title}
        )
        
        # 4. Trigger re-evaluation of downstream dependencies
        # Any items depending on this might now be READY instead of BLOCKED
        for dependent_link in item.dependent_items.all():
            ExecutionEligibilityService.update_item_mode(dependent_link.item, user)
            
        # 5. Update progress
        CareerProgressEngine.calculate_progress(user)
        
        return item

class NextBestActionService:
    @staticmethod
    def get_next_action(user):
        """
        Determines the single most impactful NEXT action the user should take.
        Excludes BLOCKED items.
        """
        plan = CareerExecutionPlan.objects.filter(user=user).first()
        if not plan:
            return None
            
        # Eligible for next action: READY, PENDING, WAITING_FOR_USER, WAITING_FOR_SYSTEM, REVIEW_REQUIRED
        # Exclude: BLOCKED, COMPLETED, FAILED, CANCELLED, EXPIRED, SUPERSEDED
        eligible_items = plan.items.exclude(
            status__in=[
                ExecutionStatus.BLOCKED, ExecutionStatus.COMPLETED,
                ExecutionStatus.FAILED, ExecutionStatus.CANCELLED,
                ExecutionStatus.EXPIRED, ExecutionStatus.SUPERSEDED,
                ExecutionStatus.IN_PROGRESS
            ]
        ).order_by('-final_score', '-impact_score')
        
        return eligible_items.first()
