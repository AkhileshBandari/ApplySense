from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProfileRetrieveUpdateView, ExperienceViewSet,
    EducationViewSet, CertificationViewSet, SkillViewSet
)

router = DefaultRouter()
router.register('experiences', ExperienceViewSet, basename='experience')
router.register('educations', EducationViewSet, basename='education')
router.register('certifications', CertificationViewSet, basename='certification')
router.register('skills', SkillViewSet, basename='skill')

urlpatterns = [
    path('', ProfileRetrieveUpdateView.as_view(), name='profile_detail'),
    path('', include(router.urls)),
]
