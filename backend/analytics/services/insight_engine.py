from .kpi_service import get_overview_kpis
from .performance_service import get_sources_analytics, get_resumes_analytics, get_match_score_analytics

MIN_COMPARISON_SAMPLE_SIZE = 10

def generate_insights(user, validated_data):
    insights = []
    
    # 1. Overall KPIs
    kpis = get_overview_kpis(user, validated_data)
    
    if kpis['applications_submitted'] > MIN_COMPARISON_SAMPLE_SIZE:
        if kpis['response_rate'] < 5.0:
            insights.append({
                "type": "LOW_RESPONSE_RATE",
                "severity": "WARNING",
                "title": "Low Overall Response Rate",
                "evidence": {
                    "submitted": kpis['applications_submitted'],
                    "responses": kpis['responses'],
                    "response_rate": kpis['response_rate']
                },
                "description": f"Your response rate is {kpis['response_rate']}%. Consider reviewing your baseline resume or targeting higher match score roles."
            })
            
        if kpis['interview_rate'] > 20.0:
            insights.append({
                "type": "HIGH_INTERVIEW_CONVERSION",
                "severity": "SUCCESS",
                "title": "High Interview Conversion",
                "evidence": {
                    "submitted": kpis['applications_submitted'],
                    "interviews": kpis['interviews'],
                    "interview_rate": kpis['interview_rate']
                },
                "description": f"Your interview conversion rate of {kpis['interview_rate']}% is very strong."
            })
            
    # 2. Source Performance
    sources = get_sources_analytics(user, validated_data)
    for s in sources:
        if s['submitted'] >= MIN_COMPARISON_SAMPLE_SIZE:
            if s['interview_rate'] > kpis['interview_rate'] * 1.5 and s['interview_rate'] > 10.0:
                insights.append({
                    "type": "SOURCE_OUTPERFORMING",
                    "severity": "INFO",
                    "title": f"Source Outperforming: {s['dimension']}",
                    "evidence": s,
                    "description": f"Applications from {s['dimension']} yield a {s['interview_rate']}% interview rate, significantly higher than your {kpis['interview_rate']}% average."
                })
                
    # 3. Match Score Performance
    match_scores = get_match_score_analytics(user, validated_data)
    high_match = next((b for b in match_scores if b['bucket'] == '80-89' or b['bucket'] == '90-100'), None)
    low_match = next((b for b in match_scores if b['bucket'] == '0-49' or b['bucket'] == '50-59'), None)
    
    if high_match and high_match['submitted'] >= MIN_COMPARISON_SAMPLE_SIZE and low_match and low_match['submitted'] >= MIN_COMPARISON_SAMPLE_SIZE:
        if high_match['interview_rate'] > low_match['interview_rate']:
            insights.append({
                "type": "MATCH_SCORE_CORRELATION",
                "severity": "INFO",
                "title": "High Match Scores Yield More Interviews",
                "evidence": {
                    "high_match": high_match,
                    "low_match": low_match
                },
                "description": f"Your {high_match['bucket']} match score applications produced an interview rate of {high_match['interview_rate']}%, compared to {low_match['interview_rate']}% for lower scores."
            })
            
    return insights
