from django.db.models import Count, Q
from .base import get_base_application_qs
from .kpi_service import SUBMITTED_STATES, RESPONSE_STATES, INTERVIEW_STATES, OFFER_STATES, REJECTED_STATES

def safe_div(num, den):
    if not den: return 0.0
    return round((num / den) * 100, 1)

def get_performance_by_dimension(app_qs, dimension_field):
    # Base aggregation grouped by dimension
    aggregates = app_qs.values(dimension_field).annotate(
        applications=Count('id'),
        submitted=Count('id', filter=Q(status__in=SUBMITTED_STATES)),
        responses=Count('id', filter=Q(status__in=RESPONSE_STATES)),
        interviews=Count('id', filter=Q(status__in=INTERVIEW_STATES)),
        offers=Count('id', filter=Q(status__in=OFFER_STATES)),
        rejections=Count('id', filter=Q(status__in=REJECTED_STATES)),
    ).order_by('-submitted')
    
    results = []
    for agg in aggregates:
        dimension_val = agg[dimension_field] if agg[dimension_field] else 'Unknown'
        submitted = agg['submitted']
        results.append({
            "dimension": dimension_val,
            "applications": agg['applications'],
            "submitted": submitted,
            "responses": agg['responses'],
            "interviews": agg['interviews'],
            "offers": agg['offers'],
            "rejections": agg['rejections'],
            "response_rate": safe_div(agg['responses'], submitted),
            "interview_rate": safe_div(agg['interviews'], submitted),
            "offer_rate": safe_div(agg['offers'], submitted),
            "rejection_rate": safe_div(agg['rejections'], submitted),
        })
    return results

def get_sources_analytics(user, validated_data):
    app_qs = get_base_application_qs(user, validated_data)
    return get_performance_by_dimension(app_qs, 'source')

def get_providers_analytics(user, validated_data):
    app_qs = get_base_application_qs(user, validated_data)
    return get_performance_by_dimension(app_qs, 'application_provider')

def get_resumes_analytics(user, validated_data):
    app_qs = get_base_application_qs(user, validated_data)
    return get_performance_by_dimension(app_qs, 'resume_version__version_name')

def get_markets_analytics(user, validated_data):
    app_qs = get_base_application_qs(user, validated_data)
    return get_performance_by_dimension(app_qs, 'job__country')

def get_match_score_analytics(user, validated_data):
    app_qs = get_base_application_qs(user, validated_data)
    
    # Bucket manually in Python since dynamic bucketing in SQL varies by DB
    buckets = {
        "0-49": {"applications": 0, "submitted": 0, "responses": 0, "interviews": 0, "offers": 0, "rejections": 0},
        "50-59": {"applications": 0, "submitted": 0, "responses": 0, "interviews": 0, "offers": 0, "rejections": 0},
        "60-69": {"applications": 0, "submitted": 0, "responses": 0, "interviews": 0, "offers": 0, "rejections": 0},
        "70-79": {"applications": 0, "submitted": 0, "responses": 0, "interviews": 0, "offers": 0, "rejections": 0},
        "80-89": {"applications": 0, "submitted": 0, "responses": 0, "interviews": 0, "offers": 0, "rejections": 0},
        "90-100": {"applications": 0, "submitted": 0, "responses": 0, "interviews": 0, "offers": 0, "rejections": 0}
    }
    
    apps = app_qs.values('match_score', 'status')
    for app in apps:
        score = app['match_score'] or 0
        if score < 50: b = "0-49"
        elif score < 60: b = "50-59"
        elif score < 70: b = "60-69"
        elif score < 80: b = "70-79"
        elif score < 90: b = "80-89"
        else: b = "90-100"
        
        status = app['status']
        buckets[b]['applications'] += 1
        if status in SUBMITTED_STATES: buckets[b]['submitted'] += 1
        if status in RESPONSE_STATES: buckets[b]['responses'] += 1
        if status in INTERVIEW_STATES: buckets[b]['interviews'] += 1
        if status in OFFER_STATES: buckets[b]['offers'] += 1
        if status in REJECTED_STATES: buckets[b]['rejections'] += 1
        
    results = []
    for b, data in buckets.items():
        submitted = data['submitted']
        results.append({
            "bucket": b,
            "applications": data['applications'],
            "submitted": submitted,
            "responses": data['responses'],
            "interviews": data['interviews'],
            "offers": data['offers'],
            "rejections": data['rejections'],
            "response_rate": safe_div(data['responses'], submitted),
            "interview_rate": safe_div(data['interviews'], submitted),
        })
    return results
