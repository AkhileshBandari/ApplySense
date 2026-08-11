from django.urls import path, include
from rest_framework.routers import DefaultRouter
from career_outcomes.views import CareerOutcomeViewSet, CareerOutcomeSnapshotViewSet

router = DefaultRouter()
router.register(r'events', CareerOutcomeViewSet, basename='career-outcome-event')
router.register(r'snapshots', CareerOutcomeSnapshotViewSet, basename='career-outcome-snapshot')

urlpatterns = [
    path('', include(router.urls)),
]
