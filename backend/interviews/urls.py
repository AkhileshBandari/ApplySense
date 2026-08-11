from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InterviewPlanViewSet, MockInterviewSessionViewSet, InterviewAnalyticsViewSet

router = DefaultRouter()
router.register(r'plans', InterviewPlanViewSet, basename='interview-plan')
router.register(r'sessions', MockInterviewSessionViewSet, basename='interview-session')

urlpatterns = [
    path('', include(router.urls)),
    path('readiness/', InterviewAnalyticsViewSet.as_view({'get': 'readiness'}), name='interview-readiness'),
    path('weaknesses/', InterviewAnalyticsViewSet.as_view({'get': 'weaknesses'}), name='interview-weaknesses'),
]
