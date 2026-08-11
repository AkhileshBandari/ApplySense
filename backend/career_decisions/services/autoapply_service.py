class AutoApplyEligibilityService:
    """
    Enforces Phase 5F automation safety boundaries before allowing an action
    to transition to AUTO_EXECUTABLE.
    """
    @staticmethod
    def is_eligible_for_automation(action, user) -> bool:
        # Check if the user even has automation enabled
        # Usually from `automation.models.AutomationPolicy`
        try:
            from automation.models import AutomationPolicy
            policy = AutomationPolicy.objects.get(user=user)
            if not policy.is_active or policy.global_pause:
                return False
        except Exception:
            return False
            
        # Ensure dependencies are cleared
        if action.dependencies.filter(depends_on__status__in=['PENDING', 'IN_PROGRESS', 'FAILED']).exists():
            return False
            
        # Must pass Phase 5 safety rules
        # (placeholder for integration logic)
        
        return True
