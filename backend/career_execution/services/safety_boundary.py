from career_execution.models import CareerExecutionItem, ExecutionMode, ExecutionStatus
from career_decisions.services.autoapply_service import AutoApplyEligibilityService

class ExecutionEligibilityService:
    """
    Evaluates whether an action can safely transition to AUTO_EXECUTABLE or remain in a ready state.
    """
    
    @staticmethod
    def evaluate_eligibility(item: CareerExecutionItem, user) -> str:
        """
        Returns the appropriate execution mode (USER_ACTION, AUTO_EXECUTABLE, REVIEW_REQUIRED, etc.)
        """
        # If the item depends on anything not COMPLETED, it is BLOCKED.
        if item.dependencies.filter(depends_on__status__in=[
            ExecutionStatus.PENDING, ExecutionStatus.READY, ExecutionStatus.BLOCKED,
            ExecutionStatus.IN_PROGRESS, ExecutionStatus.WAITING_FOR_USER,
            ExecutionStatus.WAITING_FOR_SYSTEM, ExecutionStatus.REVIEW_REQUIRED,
            ExecutionStatus.FAILED, ExecutionStatus.CANCELLED
        ]).exists():
            return ExecutionMode.BLOCKED
            
        # Re-evaluate based on the source action type if present
        if item.action_type == 'AUTO_EXECUTABLE' or item.source_action and item.source_action.action_type == 'AUTO_EXECUTABLE':
            # Strict boundary: re-verify AutoApplyEligibilityService
            if item.source_action:
                is_eligible = AutoApplyEligibilityService.is_eligible_for_automation(item.source_action, user)
                if is_eligible:
                    return ExecutionMode.AUTO_EXECUTABLE
                else:
                    return ExecutionMode.REVIEW_REQUIRED
            else:
                # If no source action, we cannot prove automation is safe. Fallback.
                return ExecutionMode.USER_ACTION
                
        if item.action_type == 'REVIEW_REQUIRED' or item.source_action and item.source_action.action_type == 'REVIEW_REQUIRED':
            return ExecutionMode.REVIEW_REQUIRED
            
        if item.action_type == 'INFORMATIONAL':
            return ExecutionMode.SYSTEM_OBSERVATION
            
        return ExecutionMode.USER_ACTION

    @staticmethod
    def update_item_mode(item: CareerExecutionItem, user):
        new_mode = ExecutionEligibilityService.evaluate_eligibility(item, user)
        if item.execution_mode != new_mode:
            item.execution_mode = new_mode
            if new_mode == ExecutionMode.BLOCKED and item.status not in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED, ExecutionStatus.SUPERSEDED]:
                item.status = ExecutionStatus.BLOCKED
            elif new_mode != ExecutionMode.BLOCKED and item.status == ExecutionStatus.BLOCKED:
                item.status = ExecutionStatus.READY
            item.save()
            return True
        return False
