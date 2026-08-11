from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.db.models import Count, Min, F
from applications.models import ApplicationStatusHistory
from .base import get_base_application_qs
from .kpi_service import SUBMITTED_STATES, RESPONSE_STATES, INTERVIEW_STATES, OFFER_STATES

def get_trends_analytics(user, validated_data):
    app_qs = get_base_application_qs(user, validated_data)
    
    # Decide grouping based on time_range
    time_range = validated_data.get('time_range', '30_DAYS')
    if time_range in ['7_DAYS', '30_DAYS']:
        trunc_func = TruncDay
    elif time_range in ['90_DAYS', '6_MONTHS']:
        trunc_func = TruncWeek
    else:
        trunc_func = TruncMonth
        
    velocity = (
        app_qs
        .filter(status__in=SUBMITTED_STATES, submitted_at__isnull=False)
        .annotate(period=trunc_func('submitted_at'))
        .values('period')
        .annotate(count=Count('id'))
        .order_by('period')
    )
    
    trend_data = []
    for item in velocity:
        trend_data.append({
            "period": item['period'].isoformat() if item['period'] else None,
            "submissions": item['count']
        })
        
    # Calculate Time to Response/Interview/Offer using History
    submitted_apps = app_qs.filter(status__in=SUBMITTED_STATES, submitted_at__isnull=False)
    
    def calculate_time_to_state(target_states):
        histories = ApplicationStatusHistory.objects.filter(
            application__in=submitted_apps,
            new_status__in=target_states
        ).values('application_id').annotate(
            first_reached=Min('timestamp')
        )
        
        # We need the application's submitted_at to calculate the delta
        app_submits = {
            app['id']: app['submitted_at']
            for app in submitted_apps.values('id', 'submitted_at')
        }
        
        deltas = []
        for h in histories:
            app_id = h['application_id']
            if app_id in app_submits and app_submits[app_id] and h['first_reached']:
                delta = (h['first_reached'] - app_submits[app_id]).total_seconds() / 86400.0 # in days
                if delta >= 0:
                    deltas.append(delta)
                    
        if not deltas:
            return None, None
            
        import statistics
        return round(statistics.mean(deltas), 1), round(statistics.median(deltas), 1)

    mean_resp, median_resp = calculate_time_to_state(RESPONSE_STATES)
    mean_int, median_int = calculate_time_to_state(INTERVIEW_STATES)
    mean_off, median_off = calculate_time_to_state(OFFER_STATES)

    return {
        "velocity": trend_data,
        "time_to_response_days": {"average": mean_resp, "median": median_resp},
        "time_to_interview_days": {"average": mean_int, "median": median_int},
        "time_to_offer_days": {"average": mean_off, "median": median_off},
    }
