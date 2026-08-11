from django.utils import timezone
from datetime import timedelta
from applications.models import Application
from jobs.models import Job

def get_date_range(time_range, start_date_str=None, end_date_str=None):
    now = timezone.now()
    if time_range == '7_DAYS':
        return now - timedelta(days=7), now
    elif time_range == '30_DAYS':
        return now - timedelta(days=30), now
    elif time_range == '90_DAYS':
        return now - timedelta(days=90), now
    elif time_range == '6_MONTHS':
        return now - timedelta(days=180), now
    elif time_range == '1_YEAR':
        return now - timedelta(days=365), now
    elif time_range == 'CUSTOM' and start_date_str and end_date_str:
        # Assuming ISO format strings for custom, though serializer would parse it
        pass # The serializer handles datetime parsing
    return None, None # ALL_TIME

def apply_filters(queryset, time_range, start_date=None, end_date=None, country=None, source=None, provider=None, date_field='created_at'):
    start, end = get_date_range(time_range)
    if start_date and end_date and time_range == 'CUSTOM':
        start, end = start_date, end_date
        
    if start and end:
        queryset = queryset.filter(**{f"{date_field}__gte": start, f"{date_field}__lte": end})
        
    if country:
        # Assuming job__country for Application queryset
        if queryset.model == Application:
            queryset = queryset.filter(job__country=country)
        elif queryset.model == Job:
            queryset = queryset.filter(country=country)
            
    if source:
        if queryset.model == Application:
            queryset = queryset.filter(source=source)
        elif queryset.model == Job:
            queryset = queryset.filter(source=source)
            
    if provider:
        if queryset.model == Application:
            queryset = queryset.filter(application_provider=provider)
        elif queryset.model == Job:
            queryset = queryset.filter(application_provider=provider)
            
    return queryset

def get_base_application_qs(user, validated_data):
    qs = Application.objects.filter(user=user)
    return apply_filters(
        qs, 
        validated_data.get('time_range'),
        validated_data.get('start_date'),
        validated_data.get('end_date'),
        validated_data.get('country'),
        validated_data.get('source'),
        validated_data.get('provider'),
        date_field='created_at'
    )
