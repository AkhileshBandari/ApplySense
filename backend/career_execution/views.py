from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from career_execution.models import CareerExecutionPlan, CareerExecutionItem, CareerExecutionProgress, ExecutionStatus
from career_execution.serializers import CareerExecutionPlanSerializer, CareerExecutionItemSerializer, CareerExecutionProgressSerializer
from career_execution.services.reconciliation_service import ActionReconciliationService
from career_execution.services.progress_engine import CareerProgressEngine
from career_execution.services.execution_service import NextBestActionService, ExecutionLifecycleService

class CareerExecutionViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        # Always reconcile first to ensure we have the latest Phase 7G decisions
        plan = ActionReconciliationService.reconcile_plan(request.user)
        if not plan:
            return Response({"detail": "No career decision plan found. Please generate one first."}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = CareerExecutionPlanSerializer(plan)
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'])
    def progress(self, request):
        progress = CareerExecutionProgress.objects.filter(user=request.user).order_by('-timestamp').first()
        if not progress:
            progress = CareerProgressEngine.calculate_progress(request.user)
        serializer = CareerExecutionProgressSerializer(progress)
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'])
    def next_action(self, request):
        # Reconcile first
        ActionReconciliationService.reconcile_plan(request.user)
        item = NextBestActionService.get_next_action(request.user)
        if not item:
            return Response({"detail": "No actionable items available."}, status=status.HTTP_404_NOT_FOUND)
        serializer = CareerExecutionItemSerializer(item)
        return Response(serializer.data)

class CareerExecutionItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CareerExecutionItemSerializer
    
    def get_queryset(self):
        return CareerExecutionItem.objects.filter(plan__user=self.request.user).prefetch_related('dependencies__depends_on')
        
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        item = self.get_object()
        
        # In a real application, we would strictly verify evidence here before completing.
        # e.g., if item.action_type == 'INTERVIEW', check if MockInterviewSession exists.
        # For this Phase 7H implementation, we trust the frontend request but we must enforce 
        # dependency graph boundaries - cannot complete if dependencies are not met.
        
        has_blocking_deps = item.dependencies.filter(depends_on__status__in=[
            ExecutionStatus.PENDING, ExecutionStatus.READY, ExecutionStatus.BLOCKED,
            ExecutionStatus.IN_PROGRESS, ExecutionStatus.WAITING_FOR_USER,
            ExecutionStatus.WAITING_FOR_SYSTEM, ExecutionStatus.REVIEW_REQUIRED,
            ExecutionStatus.FAILED, ExecutionStatus.CANCELLED
        ]).exists()
        
        if has_blocking_deps:
            return Response({"detail": "Cannot complete action. Prerequisites are not met."}, status=status.HTTP_400_BAD_REQUEST)
            
        ExecutionLifecycleService.complete_action(item, request.user)
        return Response({"status": "action completed"})
