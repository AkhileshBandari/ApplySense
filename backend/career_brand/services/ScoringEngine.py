from career_brand.models import ProfessionalProfile
from career_brand.services.ClaimValidationService import ClaimValidationService
from typing import Dict

class ScoringEngine:
    
    @classmethod
    def calculate_completeness(cls, profile: ProfessionalProfile) -> int:
        """
        Deterministically calculates the completeness score (0-100).
        """
        score = 0
        
        # Base fields (40 points)
        if profile.headline: score += 10
        if profile.about: score += 10
        if profile.location: score += 10
        if profile.current_role: score += 10
        
        # Sections (60 points)
        section_types = set(profile.sections.values_list('section_type', flat=True))
        if 'EXPERIENCE' in section_types: score += 20
        if 'EDUCATION' in section_types: score += 10
        if 'SKILL' in section_types: score += 15
        if 'PROJECT' in section_types: score += 15
        
        return min(score, 100)

    @classmethod
    def calculate_recruiter_readiness(cls, profile: ProfessionalProfile) -> int:
        """
        Deterministically calculates recruiter readiness based on completeness and claim validity.
        """
        completeness = cls.calculate_completeness(profile)
        
        # Start with completeness as a baseline, but weight it down
        base_score = completeness * 0.5
        
        # Penalty for unsupported claims in the About section (simulated example)
        about_section = profile.sections.filter(section_type='ABOUT').first()
        penalty = 0
        bonus = 0
        if about_section:
            validation = ClaimValidationService.validate_text_claims(profile.user, about_section.raw_content)
            
            # Penalize for unsupported claims
            penalty += len(validation['unsupported']) * 5
            
            # Bonus for having verified/supported claims
            bonus += len(validation['supported']) * 5
            
        final_score = base_score + bonus - penalty
        
        # Clamp to 0-100
        return int(max(0, min(100, final_score)))
        
    @classmethod
    def calculate_keyword_alignment(cls, profile: ProfessionalProfile) -> int:
        """
        Calculates how well the profile aligns with the target role's market demand.
        """
        if not profile.target_role:
            return 0
            
        from learning.models import MarketSkillDemand
        demands = MarketSkillDemand.objects.filter(target_role=profile.target_role)
        if not demands.exists():
            return 0
            
        score = 0
        profile_skills_text = " ".join([s.raw_content for s in profile.sections.all()]).lower()
        
        for demand in demands:
            if demand.canonical_skill.lower() in profile_skills_text:
                score += (demand.required_frequency * 10)
                
        return int(min(100, score))
