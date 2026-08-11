from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProfileRetrieveUpdateView, ExperienceViewSet,
    EducationViewSet, CertificationViewSet, SkillViewSet,
    ProjectViewSet, AchievementViewSet, LanguageViewSet,
    WorkAuthorizationViewSet, CareerPreferencesView,
    ProfileCompletenessView, PendingImportView, FactReviewView
)

router = DefaultRouter()
router.register('experiences', ExperienceViewSet, basename='experience')
router.register('educations', EducationViewSet, basename='education')
router.register('certifications', CertificationViewSet, basename='certification')
router.register('skills', SkillViewSet, basename='skill')
router.register('projects', ProjectViewSet, basename='project')
router.register('achievements', AchievementViewSet, basename='achievement')
router.register('languages', LanguageViewSet, basename='language')
router.register('work_authorizations', WorkAuthorizationViewSet, basename='work_authorization')

urlpatterns = [
    path('', ProfileRetrieveUpdateView.as_view(), name='profile_detail'),
    path('preferences/', CareerPreferencesView.as_view(), name='career_preferences'),
    path('completeness/', ProfileCompletenessView.as_view(), name='profile_completeness'),
    path('pending-imports/', PendingImportView.as_view(), name='pending_imports'),
    path('fact-review/', FactReviewView.as_view(), name='fact_review'),
    path('', include(router.urls)),
]
