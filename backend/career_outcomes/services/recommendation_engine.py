from career_outcomes.services.funnel_analysis_service import FunnelAnalysisService
from django.contrib.auth import get_user_model

User = get_user_model()

class RecommendationEngineService:
    """
    Converts reliable outcome signals into suggestions.
    Recommendations are deterministic, evidence-backed, and non-authoritative.
    """
    
    @classmethod
    def generate_recommendations(cls, user: User) -> list:
        recommendations = []
        
        # 1. Analyze Funnel
        funnel = FunnelAnalysisService.calculate_funnel(user)
        
        if funnel.get("status") == "SUCCESS":
            total_apps = funnel["total_apps"]
            screening_rate = funnel["screening_rate"]
            interview_rate = funnel["interview_rate"]
            offer_rate = funnel["offer_rate"]
            confidence = funnel["confidence"]
            
            # Rule 1: Low response rate
            if screening_rate < 10.0 and total_apps >= 20:
                recommendations.append({
                    "observation": f"Low screening conversion rate ({screening_rate}%).",
                    "evidence": f"Based on {total_apps} recorded applications.",
                    "confidence": confidence,
                    "meaning": "Your application materials or targeting may not be aligning with employer expectations.",
                    "recommended_action": "Review targeting / resume alignment.",
                    "causal_claim_allowed": False
                })
                
            # Rule 2: Good response, poor interviews
            if screening_rate >= 15.0 and interview_rate < 5.0 and total_apps >= 20:
                recommendations.append({
                    "observation": f"Strong screening rate ({screening_rate}%) but low interview conversion ({interview_rate}%).",
                    "evidence": f"Based on {total_apps} recorded applications.",
                    "confidence": confidence,
                    "meaning": "Employers are interested in your profile, but initial screens are not converting to full interviews.",
                    "recommended_action": "Improve initial screening and behavioral interview preparation.",
                    "causal_claim_allowed": False
                })
                
            # Rule 3: Strong interviews, no offers
            # We use absolute counts here since rates can be tricky if they haven't logged offers yet
            # but they have logged many interviews
            if funnel.get("total_interviews", 0) >= 5 and funnel.get("total_offers", 0) == 0:
                recommendations.append({
                    "observation": f"Completed {funnel['total_interviews']} interviews with 0 offers.",
                    "evidence": f"Based on {funnel['total_interviews']} recorded interviews.",
                    "confidence": confidence,
                    "meaning": "You are passing the resume and screening phases consistently, but encountering blockers in deep technical or final stages.",
                    "recommended_action": "Investigate final-round and technical performance.",
                    "causal_claim_allowed": False
                })
                
        return recommendations
