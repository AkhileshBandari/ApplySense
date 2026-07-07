from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApplicationViewSet, InterviewViewSet, ApplicationNoteViewSet, AnalyticsView

router = DefaultRouter()
router.register('tracker', ApplicationViewSet, basename='application-tracker')
router.register('interviews', InterviewViewSet, basename='application-interview')
router.register('notes', ApplicationNoteViewSet, basename='application-note')

urlpatterns = [
    path('analytics/', AnalyticsView.as_view(), name='application_analytics'),
    path('', include(router.urls)),
]
