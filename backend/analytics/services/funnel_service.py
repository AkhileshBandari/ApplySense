from django.db.models import Count, Q
from .base import get_base_application_qs, apply_filters
from jobs.models import JobMatch
from .kpi_service import SUBMITTED_STATES, RESPONSE_STATES, INTERVIEW_STATES, OFFER_STATES

def get_funnel_analytics(user, validated_data):
    app_qs = get_base_application_qs(user, validated_data)
    
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
    
    matched = match_qs.count()
    
    aggregates = app_qs.aggregate(
        prepared=Count('id', filter=Q(status__in=['PREPARING', 'REVIEW_REQUIRED', 'READY_TO_SUBMIT', 'SUBMITTING'] + SUBMITTED_STATES)),
        submitted=Count('id', filter=Q(status__in=SUBMITTED_STATES)),
        response=Count('id', filter=Q(status__in=RESPONSE_STATES)),
        assessment=Count('id', filter=Q(status__in=['ASSESSMENT'] + INTERVIEW_STATES)),
        interview=Count('id', filter=Q(status__in=INTERVIEW_STATES)),
        final_round=Count('id', filter=Q(status__in=['FINAL_ROUND'] + OFFER_STATES)),
        offer=Count('id', filter=Q(status__in=OFFER_STATES)),
        accepted=Count('id', filter=Q(status='ACCEPTED')),
    )
    
    # Calculate unique conversion between adjacent stages where denominator is safe
    funnel = [
        {"stage": "Matched", "count": matched},
        {"stage": "Prepared", "count": aggregates["prepared"]},
        {"stage": "Submitted", "count": aggregates["submitted"]},
        {"stage": "Response", "count": aggregates["response"]},
        {"stage": "Assessment", "count": aggregates["assessment"]},
        {"stage": "Interview", "count": aggregates["interview"]},
        {"stage": "Final Round", "count": aggregates["final_round"]},
        {"stage": "Offer", "count": aggregates["offer"]},
        {"stage": "Accepted", "count": aggregates["accepted"]},
    ]
    
    for i in range(len(funnel)):
        if i == 0:
            funnel[i]["conversion_from_previous"] = 100.0
        else:
            prev_count = funnel[i-1]["count"]
            curr_count = funnel[i]["count"]
            if prev_count > 0:
                funnel[i]["conversion_from_previous"] = round((curr_count / prev_count) * 100, 1)
            else:
                funnel[i]["conversion_from_previous"] = 0.0
                
    return funnel
