from django.contrib.auth import get_user_model
from career_brand.services.ClaimValidationService import ClaimValidationService
from typing import Dict, Optional

User = get_user_model()

class ProfileOptimizationService:
    """
    Generates AI proposals for professional profiles and forces them through the validation loop.
    """
    
    @classmethod
    def generate_headline_proposal(cls, user: User, target_role: str) -> Optional[str]:
        """
        In a full implementation, this calls an LLM strictly bounded by the CandidateContext.
        For this deterministic test implementation, we simulate it.
        """
        # Simulated LLM output
        simulated_output = f"{target_role} | Python & Docker Expert"
        
        # VALIDATION BOUNDARY
        validation_result = ClaimValidationService.validate_generated_proposal(user, simulated_output)
        
        if not validation_result['is_safe']:
            # The AI hallucinated unsupported claims (e.g. Docker, if not verified)
            # In a real system we might retry or return an error.
            return None 
            
        return simulated_output
        
    @classmethod
    def analyze_profile(cls, user: User, profile) -> Dict:
        """
        Top-level orchestrator that runs scoring and creates recommendations.
        """
        from career_brand.services.ScoringEngine import ScoringEngine
        from career_brand.models import ProfessionalProfileAnalysis, ProfessionalProfileRecommendation
        
        from career_brand.serializers import ProfessionalProfileSerializer
        
        # 1. Score
        completeness = ScoringEngine.calculate_completeness(profile)
        readiness = ScoringEngine.calculate_recruiter_readiness(profile)
        keyword_alignment = ScoringEngine.calculate_keyword_alignment(profile)
        
        snapshot = ProfessionalProfileSerializer(profile).data
        
        analysis = ProfessionalProfileAnalysis.objects.create(
            user=user,
            profile=profile,
            target_role=profile.target_role,
            completeness_score=completeness,
            recruiter_readiness_score=readiness,
            keyword_alignment_score=keyword_alignment,
            overall_score=(completeness + readiness + keyword_alignment) // 3,
            snapshot=snapshot
        )
        
        # 2. Generate Recommendations (Deterministic)
        # E.g. Missing summary
        if not profile.about:
            ProfessionalProfileRecommendation.objects.create(
                analysis=analysis,
                section_type='ABOUT',
                recommendation_type='MISSING_ABOUT',
                severity='HIGH',
                reason_code='ABOUT_EMPTY',
                explanation='You have no About section. This hurts recruiter searchability.'
            )
            
        return analysis
