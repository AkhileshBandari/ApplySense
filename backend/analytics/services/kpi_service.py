from django.db.models import Count, Q
from applications.models import Application
from jobs.models import Job
from .base import get_base_application_qs, apply_filters

SUBMITTED_STATES = [
    'SUBMITTED', 'UNDER_REVIEW', 'ASSESSMENT', 'INTERVIEW', 
    'FINAL_ROUND', 'OFFER', 'REJECTED', 'ACCEPTED', 'DECLINED'
]

# Meaningful progression beyond just "we received it"
RESPONSE_STATES = [
    'ASSESSMENT', 'INTERVIEW', 'FINAL_ROUND', 'OFFER', 
    'REJECTED', 'ACCEPTED', 'DECLINED'
]

INTERVIEW_STATES = [
    'INTERVIEW', 'FINAL_ROUND', 'OFFER', 'ACCEPTED', 'DECLINED'
]

OFFER_STATES = [
    'OFFER', 'ACCEPTED', 'DECLINED'
]

REJECTED_STATES = ['REJECTED']

def get_overview_kpis(user, validated_data):
    app_qs = get_base_application_qs(user, validated_data)
    
    # Jobs Discovered needs to be filtered similarly
    job_qs = Job.objects.all()
    job_qs = apply_filters(
        job_qs,
        validated_data.get('time_range'),
        validated_data.get('start_date'),
        validated_data.get('end_date'),
        validated_data.get('country'),
        validated_data.get('source'),
        validated_data.get('provider'),
        date_field='discovered_at'
    )
    # The prompt says jobs_discovered but jobs don't have a direct relation to user unless through SavedJob or Application or JobMatch
    # Let's count jobs matched for this user
    from jobs.models import JobMatch
    match_qs = JobMatch.objects.filter(user=user)
    match_qs = apply_filters(
        match_qs,
        validated_data.get('time_range'),
        validated_data.get('start_date'),
        validated_data.get('end_date'),
        validated_data.get('country'),
        validated_data.get('source'),
        validated_data.get('provider'),
        date_field='created_at'
    )
    
    total_jobs_matched = match_qs.count()
    
    # Aggregations
    aggregates = app_qs.aggregate(
        applications_created=Count('id'),
        applications_submitted=Count('id', filter=Q(status__in=SUBMITTED_STATES)),
        responses=Count('id', filter=Q(status__in=RESPONSE_STATES)),
        interviews=Count('id', filter=Q(status__in=INTERVIEW_STATES)),
        offers=Count('id', filter=Q(status__in=OFFER_STATES)),
        rejections=Count('id', filter=Q(status__in=REJECTED_STATES)),
    )
    
    # Calculate Rates
    submitted = aggregates['applications_submitted']
    
    def safe_div(num, den):
        if not den: return 0.0
        return round((num / den) * 100, 1)
        
    return {
        "total_jobs_matched": total_jobs_matched,
        "applications_created": aggregates['applications_created'],
        "applications_submitted": submitted,
        "responses": aggregates['responses'],
        "interviews": aggregates['interviews'],
        "offers": aggregates['offers'],
        "rejections": aggregates['rejections'],
        
        "response_rate": safe_div(aggregates['responses'], submitted),
        "interview_rate": safe_div(aggregates['interviews'], submitted),
        "offer_rate": safe_div(aggregates['offers'], submitted),
        "rejection_rate": safe_div(aggregates['rejections'], submitted),
    }
