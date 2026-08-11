from django.urls import path
from . import views

urlpatterns = [
    path('overview/', views.overview_analytics, name='analytics-overview'),
    path('funnel/', views.funnel_analytics, name='analytics-funnel'),
    path('trends/', views.trends_analytics, name='analytics-trends'),
    path('sources/', views.sources_analytics, name='analytics-sources'),
    path('providers/', views.providers_analytics, name='analytics-providers'),
    path('resumes/', views.resumes_analytics, name='analytics-resumes'),
    path('markets/', views.markets_analytics, name='analytics-markets'),
    path('automation/', views.automation_analytics, name='analytics-automation'),
    path('insights/', views.insights_analytics, name='analytics-insights'),
]
