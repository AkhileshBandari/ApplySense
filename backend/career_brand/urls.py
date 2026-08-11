from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProfessionalProfileViewSet,
    ProfessionalProfileAnalysisViewSet,
    ProfessionalProfileRecommendationViewSet,
    ProfessionalProfileVersionViewSet
)

router = DefaultRouter()
router.register(r'profiles', ProfessionalProfileViewSet, basename='professional-profile')
router.register(r'analyses', ProfessionalProfileAnalysisViewSet, basename='profile-analysis')
router.register(r'recommendations', ProfessionalProfileRecommendationViewSet, basename='profile-recommendation')
router.register(r'versions', ProfessionalProfileVersionViewSet, basename='profile-version')

urlpatterns = [
    path('', include(router.urls)),
]
