from django.db.models import Count, Q
from automation.models import AutoApplyRunItem, UserActionRequired
from applications.models import Application
from .base import get_base_application_qs, apply_filters
from .kpi_service import SUBMITTED_STATES, RESPONSE_STATES, INTERVIEW_STATES, OFFER_STATES, REJECTED_STATES

def safe_div(num, den):
    if not den: return 0.0
    return round((num / den) * 100, 1)

def get_automation_analytics(user, validated_data):
    app_qs = get_base_application_qs(user, validated_data)
    
    # 1. Manual vs Auto
    auto_submitted = app_qs.filter(
        status__in=SUBMITTED_STATES, 
        application_mode__icontains='AUTO' # Assuming mode contains AUTO for automated runs
    )
    manual_submitted = app_qs.filter(status__in=SUBMITTED_STATES).exclude(application_mode__icontains='AUTO')
    
    def get_stats(qs):
        agg = qs.aggregate(
            submitted=Count('id'),
            responses=Count('id', filter=Q(status__in=RESPONSE_STATES)),
            interviews=Count('id', filter=Q(status__in=INTERVIEW_STATES)),
            offers=Count('id', filter=Q(status__in=OFFER_STATES)),
            rejections=Count('id', filter=Q(status__in=REJECTED_STATES)),
        )
        sub = agg['submitted']
        return {
            "submitted": sub,
            "responses": agg['responses'],
            "interviews": agg['interviews'],
            "offers": agg['offers'],
            "rejections": agg['rejections'],
            "response_rate": safe_div(agg['responses'], sub),
            "interview_rate": safe_div(agg['interviews'], sub),
            "offer_rate": safe_div(agg['offers'], sub),
            "rejection_rate": safe_div(agg['rejections'], sub),
        }
        
    manual_vs_auto = {
        "auto": get_stats(auto_submitted),
        "manual": get_stats(manual_submitted)
    }
    
    # 2. Policy Block Analytics
    run_items = AutoApplyRunItem.objects.filter(run__user=user)
    run_items = apply_filters(
        run_items,
        validated_data.get('time_range'),
        validated_data.get('start_date'),
        validated_data.get('end_date'),
        validated_data.get('country'),
        validated_data.get('source'),
        validated_data.get('provider'),
        date_field='created_at'
    )
    
    blocks = run_items.filter(decision='BLOCKED').values('reason_code').annotate(count=Count('id')).order_by('-count')
    policy_blocks = [{"reason": b['reason_code'] or 'UNKNOWN', "count": b['count']} for b in blocks]
    
    # 3. User Action Required Analytics
    uar_qs = UserActionRequired.objects.filter(user=user)
    uar_qs = apply_filters(
        uar_qs,
        validated_data.get('time_range'),
        validated_data.get('start_date'),
        validated_data.get('end_date'),
        validated_data.get('country'),
        validated_data.get('source'),
        validated_data.get('provider'),
        date_field='created_at'
    )
    
    uars = uar_qs.values('reason').annotate(count=Count('id')).order_by('-count')
    user_actions = [{"reason": u['reason'] or 'UNKNOWN', "count": u['count']} for u in uars]
    
    # 4. Automation Success Rate
    # total items that attempted execution vs total items that succeeded
    exec_attempts = run_items.filter(stage='EXECUTION').count()
    exec_success = run_items.filter(stage='EXECUTION', decision='SUCCESS').count()
    
    success_rate = safe_div(exec_success, exec_attempts)
    
    return {
        "manual_vs_auto": manual_vs_auto,
        "policy_blocks": policy_blocks,
        "user_actions": user_actions,
        "automation_success": {
            "attempts": exec_attempts,
            "success": exec_success,
            "success_rate": success_rate
        }
    }
