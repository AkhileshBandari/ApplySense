from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from career_outcomes.models import CareerOutcomeRecord, NormalizedOutcomeState
from career_outcomes.services.confidence_service import ConfidenceService

User = get_user_model()

class FunnelAnalysisService:
    """
    Builds deterministic funnel analysis preventing zero-division and generating safe rates.
    """
    
    @classmethod
    def calculate_funnel(cls, user: User, filters: dict = None) -> dict:
        qs = CareerOutcomeRecord.objects.filter(user=user)
        if filters:
            qs = qs.filter(**filters)
            
        stats = qs.aggregate(
            total_apps=Count('id', filter=Q(normalized_state__in=[
                NormalizedOutcomeState.APPLIED, NormalizedOutcomeState.SUBMITTED
            ])),
            total_screens=Count('id', filter=Q(normalized_state=NormalizedOutcomeState.SCREENING)),
            total_interviews=Count('id', filter=Q(normalized_state=NormalizedOutcomeState.INTERVIEW)),
            total_final=Count('id', filter=Q(normalized_state=NormalizedOutcomeState.FINAL_ROUND)),
            total_offers=Count('id', filter=Q(normalized_state=NormalizedOutcomeState.OFFER)),
            total_accepted=Count('id', filter=Q(normalized_state=NormalizedOutcomeState.ACCEPTED)),
            total_rejected=Count('id', filter=Q(normalized_state=NormalizedOutcomeState.REJECTED)),
        )
        
        # In a real funnel, subsequent stages imply previous stages (if they weren't logged).
        # For simplicity in this engine, we count explicit logs.
        # Safely calculate rates
        
        total_apps = stats['total_apps'] or 0
        
        if total_apps < 10:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": "Need at least 10 recorded applications for meaningful funnel analysis.",
                "total_apps": total_apps,
                "confidence": ConfidenceService.calculate_confidence(total_apps)
            }
            
        def safe_rate(numerator, denominator):
            if denominator == 0:
                return 0.0
            val = round((numerator / denominator) * 100, 2)
            return min(val, 100.0) # Cannot exceed 100%
            
        funnel = {
            "status": "SUCCESS",
            "total_apps": total_apps,
            "screening_rate": safe_rate(stats['total_screens'], total_apps),
            "interview_rate": safe_rate(stats['total_interviews'], total_apps),
            "final_round_rate": safe_rate(stats['total_final'], total_apps),
            "offer_rate": safe_rate(stats['total_offers'], total_apps),
            "acceptance_rate": safe_rate(stats['total_accepted'], stats['total_offers'] or 1),
            "rejection_rate": safe_rate(stats['total_rejected'], total_apps),
            "confidence": ConfidenceService.calculate_confidence(total_apps)
        }
        
        return funnel
