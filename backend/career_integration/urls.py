from django.urls import path, include
from rest_framework.routers import DefaultRouter
from career_integration.views import (
    CareerOperatingStateViewSet, CareerIntegrationSnapshotViewSet, CareerOutcomeEventViewSet,
    UserActionItemViewSet
)

router = DefaultRouter()
router.register(r'state', CareerOperatingStateViewSet, basename='integration-state')
router.register(r'snapshot', CareerIntegrationSnapshotViewSet, basename='integration-snapshot')
router.register(r'events', CareerOutcomeEventViewSet, basename='integration-events')
router.register(r'action-center', UserActionItemViewSet, basename='integration-actions')

urlpatterns = [
    path('', include(router.urls)),
]
