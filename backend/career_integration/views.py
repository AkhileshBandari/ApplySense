from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from career_integration.models import (
    CareerOperatingState, CareerIntegrationSnapshot, CareerOutcomeEvent
)
from career_integration.serializers import (
    CareerOperatingStateSerializer, CareerIntegrationSnapshotSerializer, CareerOutcomeEventSerializer
)
from career_integration.services.snapshot_service import IntegrationSnapshotService

class CareerOperatingStateViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CareerOperatingStateSerializer
    
    def get_queryset(self):
        return CareerOperatingState.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        state, _ = CareerOperatingState.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(state)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='os-dashboard')
    def os_dashboard(self, request):
        from career_integration.services.os_orchestrator import OSOrchestratorService
        state = OSOrchestratorService.evaluate_os_readiness(request.user)
        serializer = self.get_serializer(state)
        return Response(serializer.data)

class UserActionItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    from career_integration.serializers import UserActionItemSerializer
    serializer_class = UserActionItemSerializer
    
    def get_queryset(self):
        from career_integration.models import UserActionItem
        return UserActionItem.objects.filter(user=self.request.user)

class CareerIntegrationSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CareerIntegrationSnapshotSerializer
    
    def get_queryset(self):
        return CareerIntegrationSnapshot.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=False, methods=['post'])
    def generate(self, request):
        snapshot = IntegrationSnapshotService.generate_snapshot(request.user)
        serializer = self.get_serializer(snapshot)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CareerOutcomeEventViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CareerOutcomeEventSerializer
    
    def get_queryset(self):
        return CareerOutcomeEvent.objects.filter(user=self.request.user).order_by('-timestamp')
