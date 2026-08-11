from django.contrib.auth import get_user_model
from career_brand.models import ProfessionalProfile
from resumes.models import ResumeVersion
from typing import Dict, List

User = get_user_model()

class ConsistencyEngine:
    """
    Compares the professional profile against the approved Resume and Phase 7C data to detect conflicts.
    """
    
    @classmethod
    def detect_inconsistencies(cls, user: User, profile: ProfessionalProfile) -> List[Dict]:
        inconsistencies = []
        
        # 1. Compare against Resume
        latest_resume = ResumeVersion.objects.filter(user=user, status='APPROVED').order_by('-created_at').first()
        if latest_resume:
            resume_content = latest_resume.structured_content
            # Very basic check: If the resume specifies a target role or latest title that doesn't match
            # This is a stub for the deeper comparison logic.
            resume_latest_role = resume_content.get('latest_role', '').lower()
            profile_current_role = profile.current_role.lower()
            
            if resume_latest_role and profile_current_role and resume_latest_role != profile_current_role:
                inconsistencies.append({
                    'type': 'ROLE_MISMATCH',
                    'description': 'Your current role on your profile does not match your latest resume.',
                    'profile_value': profile.current_role,
                    'resume_value': resume_content.get('latest_role')
                })
                
        # 2. Could compare dates of employment, skills listed vs skills on resume
        # ... logic expands here ...
        
        return inconsistencies
