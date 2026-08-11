from career_decisions.models import PriorityCategory

class CareerPriorityService:
    """
    Deterministically identifies the highest impact career blockers.
    """
    
    @staticmethod
    def calculate_priorities(snapshot_data: dict) -> list:
        priorities = []
        
        # 1. Check Skill Gaps (from Phase 7B)
        pathways = snapshot_data.get('pathways', [])
        if pathways:
            top_path = pathways[0]
            if top_path['skill_score'] < 100:
                impact = 100 - top_path['skill_score']
                priorities.append({
                    "category": PriorityCategory.SKILL_GAP,
                    "severity": "HIGH" if impact > 50 else "MEDIUM",
                    "impact_score": impact,
                    "urgency": 80 if impact > 50 else 50,
                    "confidence": 90,
                    "explanation": f"Missing core skills for top path: {top_path['role_name']}.",
                    "recommended_action": "Complete missing learning roadmap items."
                })
        
        # 2. Check Career Brand
        brand_score = snapshot_data.get('career_brand_score', 0)
        if brand_score < 70:
            impact = min(100, (70 - brand_score) * 2)
            priorities.append({
                "category": PriorityCategory.CAREER_BRAND_GAP,
                "severity": "HIGH" if impact > 50 else "MEDIUM",
                "impact_score": impact,
                "urgency": 60,
                "confidence": 95,
                "explanation": "Professional profile is incomplete or lacks verification.",
                "recommended_action": "Optimize Career Brand profile."
            })
            
        # 3. Check Interview Readiness
        interview_score = snapshot_data.get('interview_readiness', 0)
        if interview_score < 60:
            impact = min(100, (60 - interview_score) * 2)
            priorities.append({
                "category": PriorityCategory.INTERVIEW_GAP,
                "severity": "HIGH" if impact > 50 else "MEDIUM",
                "impact_score": impact,
                "urgency": 90 if pathways and pathways[0].get('overall_readiness', 0) > 70 else 40,
                "confidence": 85,
                "explanation": "Interview readiness is low, risking application conversions.",
                "recommended_action": "Schedule Mock Interview Session."
            })
            
        # 4. Check Application Funnel
        funnel = snapshot_data.get('application_funnel', {})
        if funnel.get('total_applications', 0) > 20 and funnel.get('interview_rate', 0) < 5:
            priorities.append({
                "category": PriorityCategory.APPLICATION_CONVERSION,
                "severity": "HIGH",
                "impact_score": 95,
                "urgency": 100,
                "confidence": 90,
                "explanation": "High application volume but extremely low interview conversion rate.",
                "recommended_action": "Pause applications and optimize Resume / Career Brand."
            })
            
        priorities.sort(key=lambda x: x['impact_score'], reverse=True)
        return priorities
