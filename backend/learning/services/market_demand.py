from typing import Dict, List, Any
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from jobs.models import Job, JobRequirement
from learning.models import MarketSkillDemand
from learning.services.taxonomy import SkillRequirementNormalizationService

class MarketSkillDemandService:
    @staticmethod
    def get_market_aggregate(target_role: str, country_code: str = "", experience_level: str = "", min_sample_size: int = 10) -> Dict[str, Any]:
        """
        Calculates market skill demand dynamically from active Jobs matching the criteria.
        Returns a dictionary with frequencies or INSUFFICIENT_MARKET_DATA if the sample is too small.
        """
        # Base query for jobs
        jobs = Job.objects.filter(
            status='ACTIVE',
            title__icontains=target_role
        )
        if country_code:
            jobs = jobs.filter(country_code=country_code)
        
        # NOTE: For experience level we might want to map ENTRY -> experience_max <= 2, etc. 
        # Keeping it simple by relying on Job model mapping for now if available, otherwise ignoring.
        if experience_level == 'ENTRY':
            jobs = jobs.filter(experience_max__lte=2)
        elif experience_level == 'MID':
            jobs = jobs.filter(experience_min__gte=2, experience_max__lte=6)
        elif experience_level == 'SENIOR':
            jobs = jobs.filter(experience_min__gte=5)
            
        sample_size = jobs.count()
        if sample_size < min_sample_size:
            return {
                "status": "INSUFFICIENT_MARKET_DATA",
                "sample_size": sample_size,
                "skills": {}
            }
            
        # We need to fetch requirements for these jobs
        job_ids = jobs.values_list('id', flat=True)
        requirements = JobRequirement.objects.filter(job_id__in=job_ids)
        
        skill_counts = {}
        for req in requirements:
            # required_skills is a list of strings
            for skill in req.required_skills:
                canonical = SkillRequirementNormalizationService.normalize_skill(skill)
                if canonical not in skill_counts:
                    skill_counts[canonical] = {"required": 0, "preferred": 0}
                skill_counts[canonical]["required"] += 1
                
            for skill in req.preferred_skills:
                canonical = SkillRequirementNormalizationService.normalize_skill(skill)
                if canonical not in skill_counts:
                    skill_counts[canonical] = {"required": 0, "preferred": 0}
                skill_counts[canonical]["preferred"] += 1

        market_data = {}
        for skill, counts in skill_counts.items():
            market_data[skill] = {
                "required_frequency": counts["required"] / sample_size,
                "preferred_frequency": counts["preferred"] / sample_size,
            }
            
            # Cache it in the database optionally
            MarketSkillDemand.objects.update_or_create(
                target_role=target_role,
                country_code=country_code,
                experience_level=experience_level,
                canonical_skill=skill,
                defaults={
                    "sample_size": sample_size,
                    "required_frequency": counts["required"] / sample_size,
                    "preferred_frequency": counts["preferred"] / sample_size,
                }
            )

        return {
            "status": "SUCCESS",
            "sample_size": sample_size,
            "skills": market_data
        }
