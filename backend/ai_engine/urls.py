from django.urls import path
from .views import InterviewPrepView

urlpatterns = [
    path('interview-prep/', InterviewPrepView.as_view(), name='coach_interview_prep'),
]
