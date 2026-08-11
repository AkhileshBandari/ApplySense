from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ApplicationViewSet, InterviewViewSet, ApplicationNoteViewSet, 
    ApplicationQuestionViewSet, ApplicationAnswerMemoryViewSet, AnalyticsView
)

router = DefaultRouter()
router.register('tracker', ApplicationViewSet, basename='application-tracker')
router.register('interviews', InterviewViewSet, basename='application-interview')
router.register('notes', ApplicationNoteViewSet, basename='application-note')
router.register('questions', ApplicationQuestionViewSet, basename='application-question')
router.register('memory', ApplicationAnswerMemoryViewSet, basename='application-memory')

urlpatterns = [
    path('analytics/', AnalyticsView.as_view(), name='application_analytics'),
    path('', include(router.urls)),
]
