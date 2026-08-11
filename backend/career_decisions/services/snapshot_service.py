import hashlib
import json
from profiles.services.candidate_context import CandidateContextService
from career_pathways.services import CareerPathRecommendationService
from interviews.services.AnalyticsServices import InterviewReadinessService
from career_brand.models import ProfessionalProfileAnalysis
from learning.models import MarketSkillDemand
from learning.services.gap_analysis import SkillGapAnalysisService

class CareerDecisionSnapshotService:
    """
    Builds the immutable snapshot representing the user's state across all ApplySense boundaries.
    """
    
    @staticmethod
    def build_snapshot_data(user) -> dict:
        data = {}
        
        # Phase 1-2: Candidate Context
        candidate_context = CandidateContextService.get_for_user(user)
        data['candidate_context'] = candidate_context
        
        # Phase 7F: Pathways
        pathways = CareerPathRecommendationService.evaluate_paths_for_user(user)
        data['pathways'] = pathways
        
        # Phase 7E: Interview Readiness
        interview_readiness = InterviewReadinessService.calculate_readiness(user)
        data['interview_readiness'] = interview_readiness if isinstance(interview_readiness, int) else 0
        
        # Phase 7D: Career Brand
        analysis = ProfessionalProfileAnalysis.objects.filter(profile__user=user).order_by('-created_at').first()
        data['career_brand_score'] = analysis.brand_readiness_score if analysis else 0
        
        # Phase 7B: Skill Gaps
        try:
            gap_analysis = SkillGapAnalysisService.analyze_gaps(user)
            data['skill_gaps'] = gap_analysis
        except Exception:
            data['skill_gaps'] = {}
            
        # Phase 6 Analytics / Phase 5 Application Strategy
        # Phase 8 Integration: Pull real funnel metrics
        try:
            from career_outcomes.services.funnel_analysis_service import FunnelAnalysisService
            funnel = FunnelAnalysisService.calculate_funnel(user)
            
            if funnel.get("status") == "SUCCESS":
                data['application_funnel'] = {
                    "total_applications": funnel.get("total_apps", 0),
                    "response_rate": funnel.get("screening_rate", 0), # Screening is first response
                    "interview_rate": funnel.get("interview_rate", 0)
                }
            else:
                data['application_funnel'] = {
                    "total_applications": funnel.get("total_apps", 0),
                    "response_rate": 0,
                    "interview_rate": 0,
                    "status": funnel.get("status")
                }
        except Exception:
            data['application_funnel'] = {
                "total_applications": 0,
                "response_rate": 0,
                "interview_rate": 0
            }
            
        return data

    @staticmethod
    def hash_snapshot(data: dict) -> str:
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()
