from django.urls import path, include
from rest_framework.routers import DefaultRouter

from evidence.views import (
    GitHubConnectionViewSet, CandidateRepositoryViewSet, CandidateSkillEvidenceViewSet,
    EvidenceSummaryViewSet, PortfolioConnectionViewSet
)

router = DefaultRouter()
router.register(r'github/connection', GitHubConnectionViewSet, basename='github-connection')
router.register(r'github/repositories', CandidateRepositoryViewSet, basename='candidate-repository')
router.register(r'skills', CandidateSkillEvidenceViewSet, basename='skill-evidence')
router.register(r'portfolio', PortfolioConnectionViewSet, basename='portfolio-connection')
router.register(r'summary', EvidenceSummaryViewSet, basename='evidence-summary')

urlpatterns = [
    path('', include(router.urls)),
]
