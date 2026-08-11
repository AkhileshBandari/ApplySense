import logging
from django.db import transaction
from django.utils import timezone
from career_integration.models import (
    CareerOperatingState,
    CareerDomainState,
    DomainName,
    DomainStateStatus,
    SystemState,
    SystemBlocker
)
from career_integration.services.action_center import ActionCenterService
from profiles.models import Profile
from career_brand.models import ProfessionalProfile
from learning.models import SkillGapAnalysis
from applications.models import Application
from automation.models import AutoApplyRun

logger = logging.getLogger(__name__)

class OSOrchestratorService:
    """Orchestrates the End-to-End Career Operating System state."""
    
    @classmethod
    def evaluate_os_readiness(cls, user):
        """Calculates the overall system state for the user by rolling up domain states."""
        operating_state, _ = CareerOperatingState.objects.get_or_create(user=user)
        
        # Determine candidate context readiness
        has_context = Profile.objects.filter(user=user).exists()
        
        # Determine profile/resume readiness
        has_profile = ProfessionalProfile.objects.filter(user=user).exists()
        
        # Determine gap analysis readiness
        has_gaps = SkillGapAnalysis.objects.filter(user=user).exists()
        
        # Determine execution/application readiness
        active_apps = Application.objects.filter(user=user, status__in=['SUBMITTED', 'INTERVIEWING', 'OFFER']).count()
        
        new_state = SystemState.ONBOARDING
        if not has_context:
            new_state = SystemState.ONBOARDING
        elif not has_profile:
            new_state = SystemState.PROFILE_READY
        elif not has_gaps:
            new_state = SystemState.MATCHING
        elif active_apps > 0:
            new_state = SystemState.APPLICATION_ACTIVE
        else:
            new_state = SystemState.EXECUTION_READY
            
        # Update metrics
        operating_state.current_os_state = new_state
        operating_state.overall_health = DomainStateStatus.HEALTHY
        operating_state.save()
        
        # Re-evaluate user actions
        ActionCenterService.recalculate_actions(user)
        
        return operating_state
