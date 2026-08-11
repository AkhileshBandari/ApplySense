from career_decisions.models import CareerDecisionPlanVersion
from career_execution.models import (
    CareerExecutionPlan, CareerExecutionItem, CareerExecutionDependency,
    CareerExecutionEvent, ExecutionStatus
)
from career_execution.services.safety_boundary import ExecutionEligibilityService

class ActionReconciliationService:
    @staticmethod
    def reconcile_plan(user):
        """
        Takes the active CareerDecisionPlanVersion and maps it into the continuous CareerExecutionPlan.
        """
        decision_plan = CareerDecisionPlanVersion.objects.filter(user=user, is_active=True).first()
        if not decision_plan:
            return None
            
        execution_plan, created = CareerExecutionPlan.objects.get_or_create(user=user)
        
        # 1. Map existing actions to avoid duplicates
        existing_items = list(execution_plan.items.all())
        
        # 2. Iterate through decision plan actions
        new_actions = list(decision_plan.actions.all())
        item_map = {} # Maps CareerAction ID -> CareerExecutionItem
        
        for action in new_actions:
            # Look for an existing item that matches exactly
            # Matching by title and source_phase. If there's an active one, reuse it.
            match = None
            for item in existing_items:
                if item.title == action.title and item.source_phase == action.source_phase:
                    if item.status not in [ExecutionStatus.SUPERSEDED, ExecutionStatus.CANCELLED]:
                        match = item
                        break
            
            if match:
                # Update scores and source action
                match.impact_score = action.impact_score
                match.urgency_score = action.urgency_score
                match.effort_penalty = action.effort_penalty
                match.final_score = action.final_score
                match.source_action = action
                match.reason = action.reason
                match.save()
                item_map[action.id] = match
            else:
                # Create new
                new_item = CareerExecutionItem.objects.create(
                    plan=execution_plan,
                    title=action.title,
                    description=action.description,
                    action_type=action.action_type,
                    source_phase=action.source_phase,
                    impact_score=action.impact_score,
                    urgency_score=action.urgency_score,
                    effort_penalty=action.effort_penalty,
                    final_score=action.final_score,
                    source_action=action,
                    reason=action.reason
                )
                CareerExecutionEvent.objects.create(
                    user=user,
                    event_type="ACTION_CREATED",
                    item=new_item,
                    details={"title": new_item.title}
                )
                item_map[action.id] = new_item
                
        # 3. Handle obsolete items (items not in the new plan, and not completed)
        active_ids = [item.id for item in item_map.values()]
        for item in existing_items:
            if item.id not in active_ids:
                if item.status in [ExecutionStatus.PENDING, ExecutionStatus.READY, ExecutionStatus.BLOCKED]:
                    item.status = ExecutionStatus.SUPERSEDED
                    item.save()
                    CareerExecutionEvent.objects.create(
                        user=user,
                        event_type="ACTION_SUPERSEDED",
                        item=item,
                        details={"reason": "Removed from latest decision plan"}
                    )
                    
        # 4. Reconcile dependencies
        CareerExecutionDependency.objects.filter(item__plan=execution_plan).delete() # Rebuild
        
        for action in new_actions:
            item = item_map[action.id]
            for dep in action.dependencies.all():
                if dep.depends_on.id in item_map:
                    depends_on_item = item_map[dep.depends_on.id]
                    CareerExecutionDependency.objects.create(
                        item=item,
                        depends_on=depends_on_item
                    )
                    
        # 5. Evaluate eligibility for all active items
        for item in execution_plan.items.exclude(status__in=[ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED, ExecutionStatus.SUPERSEDED]):
            ExecutionEligibilityService.update_item_mode(item, user)
            
        return execution_plan
