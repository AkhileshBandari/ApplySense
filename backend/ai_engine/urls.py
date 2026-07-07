from django.urls import path
from .views import SkillGapAnalysisView, LearningRoadmapView, InterviewPrepView

urlpatterns = [
    path('analyze-skills/', SkillGapAnalysisView.as_view(), name='coach_analyze_skills'),
    path('roadmap/', LearningRoadmapView.as_view(), name='coach_roadmap'),
    path('interview-prep/', InterviewPrepView.as_view(), name='coach_interview_prep'),
]
