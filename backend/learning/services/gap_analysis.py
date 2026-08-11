from typing import Dict, List, Any
from profiles.services.candidate_context import CandidateContextService
from jobs.models import Job, JobRequirement
from learning.models import (
    SkillGapAnalysis, SkillGapItem, TargetType, GapType, PriorityBand
)
from learning.services.taxonomy import SkillRequirementNormalizationService
from learning.services.market_demand import MarketSkillDemandService

class SkillGapPriorityService:
    @staticmethod
    def calculate_priority(gap_type: str, requirement_state: str, market_frequency: float = 0.0) -> PriorityBand:
        """
        Deterministic priority calculation.
        """
        if gap_type == GapType.NO_GAP:
            return PriorityBand.LOW
            
        if requirement_state == 'REQUIRED':
            if gap_type == GapType.MISSING_SKILL:
                if market_frequency > 0.5:
                    return PriorityBand.CRITICAL
                return PriorityBand.HIGH
            elif gap_type == GapType.EXPERIENCE_GAP:
                return PriorityBand.HIGH
            elif gap_type == GapType.EVIDENCE_GAP:
                return PriorityBand.MEDIUM
        elif requirement_state == 'PREFERRED':
            if gap_type == GapType.MISSING_SKILL:
                if market_frequency > 0.3:
                    return PriorityBand.MEDIUM
                return PriorityBand.LOW
            else:
                return PriorityBand.LOW
                
        return PriorityBand.LOW

class SkillGapAnalysisService:
    @staticmethod
    def generate_analysis_for_job(user, job_id: int) -> SkillGapAnalysis:
        try:
            job = Job.objects.get(id=job_id)
            requirement = job.requirements_norm
        except (Job.DoesNotExist, JobRequirement.DoesNotExist):
            raise ValueError("Job or JobRequirements do not exist")

        context = CandidateContextService.get_for_user(user)
        
        # Save snapshots
        analysis = SkillGapAnalysis.objects.create(
            user=user,
            target_type=TargetType.SPECIFIC_JOB,
            target_job=job,
            candidate_context_snapshot=context,
            requirement_snapshot={
                "required_skills": requirement.required_skills,
                "preferred_skills": requirement.preferred_skills,
                "minimum_experience": requirement.minimum_experience
            }
        )
        
        SkillGapAnalysisService._compute_gaps(analysis, context, requirement.required_skills, requirement.preferred_skills)
        return analysis

    @staticmethod
    def generate_analysis_for_role(user, target_role: str, country_code: str = "") -> SkillGapAnalysis:
        # Use MarketSkillDemandService
        market_data = MarketSkillDemandService.get_market_aggregate(target_role, country_code)
        if market_data.get("status") == "INSUFFICIENT_MARKET_DATA":
            raise ValueError("Insufficient market data for this role")
            
        context = CandidateContextService.get_for_user(user)
        
        # Extract skills > 20% required as required, > 20% preferred as preferred
        req_skills = []
        pref_skills = []
        for skill, freqs in market_data["skills"].items():
            if freqs["required_frequency"] > 0.2:
                req_skills.append(skill)
            elif freqs["preferred_frequency"] > 0.2:
                pref_skills.append(skill)
                
        analysis = SkillGapAnalysis.objects.create(
            user=user,
            target_type=TargetType.TARGET_ROLE,
            target_role=target_role,
            country_code=country_code,
            market_sample_size=market_data["sample_size"],
            candidate_context_snapshot=context,
            requirement_snapshot={
                "required_skills": req_skills,
                "preferred_skills": pref_skills
            }
        )
        
        SkillGapAnalysisService._compute_gaps(analysis, context, req_skills, pref_skills, market_data["skills"])
        return analysis

    @staticmethod
    def _compute_gaps(analysis: SkillGapAnalysis, context: dict, required_skills: list, preferred_skills: list, market_skills: dict = None):
        # Extract candidate verified skills
        candidate_skills = [
            SkillRequirementNormalizationService.normalize_skill(s.get("name", ""))
            for s in context.get("skills", [])
        ]
        
        # Extract candidate project tech
        candidate_tech = []
        for proj in context.get("projects", []):
            tech_str = proj.get("technologies", "")
            if tech_str:
                for t in tech_str.split(','):
                    candidate_tech.append(SkillRequirementNormalizationService.normalize_skill(t.strip()))
                    
        def evaluate_skill(skill, state):
            canonical = SkillRequirementNormalizationService.normalize_skill(skill)
            
            gap_type = GapType.MISSING_SKILL
            candidate_state = 'NOT_VERIFIED'
            
            if canonical in candidate_skills:
                # Skill is present in verified context.
                # Check for evidence gap (e.g., if it needs project evidence but none exists)
                if canonical not in candidate_tech:
                    gap_type = GapType.EVIDENCE_GAP
                    candidate_state = 'VERIFIED_PARTIAL'
                else:
                    gap_type = GapType.NO_GAP
                    candidate_state = 'VERIFIED_PRESENT'
            
            market_freq = 0.0
            if market_skills and canonical in market_skills:
                market_freq = market_skills[canonical].get("required_frequency", 0.0)
                
            priority = SkillGapPriorityService.calculate_priority(gap_type, state, market_freq)
            
            # Formulate reason
            reason = f"{state} skill."
            if gap_type == GapType.MISSING_SKILL:
                reason += " No verified candidate evidence found."
            elif gap_type == GapType.EVIDENCE_GAP:
                reason += " Skill is claimed but lacks project/portfolio evidence."
                
            SkillGapItem.objects.create(
                analysis=analysis,
                canonical_skill=canonical,
                candidate_state=candidate_state,
                requirement_state=state,
                gap_type=gap_type,
                priority_band=priority,
                reason=reason
            )

        for req in required_skills:
            evaluate_skill(req, 'REQUIRED')
            
        for pref in preferred_skills:
            evaluate_skill(pref, 'PREFERRED')
