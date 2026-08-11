import logging
from typing import Dict, Any, List, Tuple
from jobs.models import Job, JobMatch
from profiles.services.candidate_context import CandidateContextService

logger = logging.getLogger(__name__)

class HybridMatcherService:
    ALGORITHM_VERSION = "1.0"
    
    @classmethod
    def match(cls, user, job: Job) -> JobMatch:
        context = CandidateContextService.get_for_user(user)
        
        # Dimensions
        skills_score, skills_details = cls._match_skills(context, job)
        exp_score, exp_details = cls._match_experience(context, job)
        location_score, location_details = cls._match_location(context, job)
        work_mode_score, work_mode_details = cls._match_work_mode(context, job)
        
        # Determine aggregate score (Weights: Skills 50%, Exp 30%, Location 10%, Work Mode 10%)
        overall = (skills_score * 0.5) + (exp_score * 0.3) + (location_score * 0.1) + (work_mode_score * 0.1)
        
        # Determine eligibility based on hard constraints
        eligibility = "POSSIBLY_ELIGIBLE"
        if overall >= 85 and not location_details.get("conflict") and not work_mode_details.get("conflict"):
            eligibility = "ELIGIBLE"
        elif overall < 50:
            eligibility = "STRETCH"
        
        # Hard conflicts downgrade to LIKELY_INELIGIBLE
        if location_details.get("conflict") or work_mode_details.get("conflict"):
            eligibility = "LIKELY_INELIGIBLE"
            
        dimension_scores = {
            "skills": skills_score,
            "experience": exp_score,
            "location": location_score,
            "work_mode": work_mode_score
        }
        
        missing_required = skills_details.get("missing_required", [])
        missing_preferred = skills_details.get("missing_preferred", [])
        
        conflicts = []
        if location_details.get("conflict"):
            conflicts.append("Location preference mismatch")
        if work_mode_details.get("conflict"):
            conflicts.append("Work mode preference mismatch")
            
        match_obj, created = JobMatch.objects.update_or_create(
            user=user,
            job=job,
            defaults={
                "overall_score": int(overall),
                "eligibility": eligibility,
                "dimension_scores": dimension_scores,
                "missing_required": missing_required,
                "missing_preferred": missing_preferred,
                "candidate_preference_conflicts": conflicts,
                "algorithm_version": cls.ALGORITHM_VERSION
            }
        )
        return match_obj

    @classmethod
    def _match_skills(cls, context: Dict[str, Any], job: Job) -> Tuple[int, Dict[str, Any]]:
        if not hasattr(job, 'requirements_norm'):
            return 50, {"missing_required": [], "missing_preferred": []} # Default if no AI parsing done
            
        req = job.requirements_norm
        candidate_skills = {s.lower() for s in context.get('skills', [])}
        
        req_skills = {s.lower() for s in req.required_skills}
        pref_skills = {s.lower() for s in req.preferred_skills}
        
        if not req_skills and not pref_skills:
            return 100, {"missing_required": [], "missing_preferred": []}
            
        matched_req = req_skills.intersection(candidate_skills)
        missing_req = req_skills.difference(candidate_skills)
        
        matched_pref = pref_skills.intersection(candidate_skills)
        missing_pref = pref_skills.difference(candidate_skills)
        
        req_score = (len(matched_req) / len(req_skills)) * 100 if req_skills else 100
        pref_score = (len(matched_pref) / len(pref_skills)) * 100 if pref_skills else 100
        
        total_score = (req_score * 0.7) + (pref_score * 0.3)
        
        return int(total_score), {
            "missing_required": list(missing_req),
            "missing_preferred": list(missing_pref)
        }

    @classmethod
    def _match_experience(cls, context: Dict[str, Any], job: Job) -> Tuple[int, Dict[str, Any]]:
        req_exp = 0
        if hasattr(job, 'requirements_norm') and job.requirements_norm.minimum_experience:
            req_exp = job.requirements_norm.minimum_experience
        elif job.experience_min:
            req_exp = job.experience_min
            
        cand_exp = 0
        for exp in context.get('experiences', []):
            if isinstance(exp, dict) and exp.get('years'):
                cand_exp += exp['years']
            elif hasattr(exp, 'years'):
                cand_exp += exp.years
                
        # Heuristic scoring
        if req_exp == 0:
            return 100, {} # No specific requirement
        
        if cand_exp >= req_exp:
            return 100, {}
        elif cand_exp >= req_exp - 1:
            return 75, {}
        elif cand_exp >= req_exp - 2:
            return 50, {}
        else:
            return 25, {}

    @classmethod
    def _match_location(cls, context: Dict[str, Any], job: Job) -> Tuple[int, Dict[str, Any]]:
        # Evaluate Location and Work Authorization constraints
        
        job_country = job.country or job.country_code
        is_remote_worldwide = job.is_remote_worldwide
        
        # 1. Location match
        pref = context.get('preferences', {})
        cand_locations = pref.get('locations', '').lower()
        relocation_willingness = pref.get('relocation_willingness', False)
        cand_remote_pref = pref.get('remote', '').lower()
        
        location_conflict = False
        location_score = 100
        
        # If job is remote worldwide, location is a match for everyone unless they strictly want on-site
        if is_remote_worldwide and cand_remote_pref == 'onsite':
            location_conflict = True
            location_score = 0
            
        elif job_country:
            # Check if job country is in candidate locations
            # Or if they are willing to relocate
            if cand_locations and job_country.lower() not in cand_locations and not relocation_willingness:
                location_conflict = True
                location_score = 0
        
        # 2. Work Authorization match
        auth_conflict = False
        work_auths = context.get('work_authorizations', [])
        
        if job.work_authorization_required and job_country:
            has_auth = False
            for wa in work_auths:
                # If they have authorization for the job's country
                if wa.get('country', '').lower() == job_country.lower():
                    # If they require sponsorship and job does not provide it
                    if wa.get('sponsorship_required') and not job.sponsorship_available:
                        continue # This authorization doesn't work for this job
                    has_auth = True
                    break
                    
            if not has_auth and work_auths:
                # Candidate has defined auths, but none match this job, and they need it.
                # However, maybe the candidate can apply if sponsorship is available and they just didn't list it?
                # The rule: "Hard downgrade if candidate lacks work authorization and job explicitly does not sponsor."
                if not job.sponsorship_available:
                    auth_conflict = True
                    location_score = 0
                    
        return location_score, {"conflict": location_conflict or auth_conflict}

    @classmethod
    def _match_work_mode(cls, context: Dict[str, Any], job: Job) -> Tuple[int, Dict[str, Any]]:
        # Same for work mode.
        return 100, {"conflict": False}
