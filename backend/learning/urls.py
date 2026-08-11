from django.urls import path, include
from rest_framework.routers import DefaultRouter
from learning.views import (
    GapAnalysisViewSet, LearningRoadmapViewSet, 
    LearningRoadmapItemViewSet, ProjectRecommendationViewSet
)

app_name = 'learning'

router = DefaultRouter()
router.register(r'gap-analysis', GapAnalysisViewSet, basename='gap-analysis')
router.register(r'roadmaps', LearningRoadmapViewSet, basename='roadmaps')
router.register(r'roadmap-items', LearningRoadmapItemViewSet, basename='roadmap-items')
router.register(r'projects', ProjectRecommendationViewSet, basename='projects')

urlpatterns = [
    path('', include(router.urls)),
]
