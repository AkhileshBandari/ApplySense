import re
from typing import Dict, List
from django.contrib.auth import get_user_model
from profiles.services.candidate_context import CandidateContextService
from evidence.models import CandidateSkillEvidence
from learning.models import SkillTaxonomy
from learning.services.taxonomy import SkillRequirementNormalizationService

User = get_user_model()

class ClaimValidationService:
    """
    Validates professional profile claims (like skills) against authoritative CandidateContext
    and Phase 7C Evidence.
    """
    
    @classmethod
    def validate_text_claims(cls, user: User, text: str) -> Dict:
        """
        Extracts skills from text and validates their support in the system.
        Returns:
            {
                'supported': [...],
                'unsupported': [...],
                'evidence_only': [...] # Has GitHub/Portfolio evidence, but not verified
            }
        """
        # 1. Extract potential skills using the taxonomy
        # We'll do a simple keyword matching for this demonstration based on canonical taxonomy
        # In a real heavy system this might use NLP or the exact same logic as resume parsing
        all_canonical_skills = list(SkillTaxonomy.objects.values_list('canonical_name', flat=True))
        
        extracted_skills = set()
        text_lower = text.lower()
        for skill in all_canonical_skills:
            # Basic word boundary search
            if re.search(rf'\b{re.escape(skill.lower())}\b', text_lower):
                extracted_skills.add(skill)
                
        # 2. Get Authoritative Context
        context = CandidateContextService.get_for_user(user)
        verified_skills = {s['name'] for s in context.get('skills', []) if s.get('verification_status') == 'VERIFIED'}
        
        # 3. Get Unverified Evidence from Phase 7C
        evidence_skills = set(CandidateSkillEvidence.objects.filter(
            user=user
        ).values_list('skill_taxonomy__canonical_name', flat=True))
        
        # 4. Classify
        supported = []
        unsupported = []
        evidence_only = []
        
        for skill in extracted_skills:
            if skill in verified_skills:
                supported.append(skill)
            elif skill in evidence_skills:
                evidence_only.append(skill)
            else:
                unsupported.append(skill)
                
        return {
            'supported': supported,
            'unsupported': unsupported,
            'evidence_only': evidence_only
        }
        
    @classmethod
    def validate_generated_proposal(cls, user: User, proposed_text: str) -> Dict:
        """
        Validates if an AI-generated proposal introduces hallucinations (unsupported claims).
        If unsupported claims exist, the proposal should be rejected.
        """
        validation = cls.validate_text_claims(user, proposed_text)
        
        is_safe = len(validation['unsupported']) == 0
        
        return {
            'is_safe': is_safe,
            'validation': validation,
            'rejection_reason': f"Unsupported claims detected: {', '.join(validation['unsupported'])}" if not is_safe else None
        }
