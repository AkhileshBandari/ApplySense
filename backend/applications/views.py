from rest_framework import viewsets, permissions, views, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Application, Interview, ApplicationNote, ApplicationAnswerMemory, ApplicationQuestion
from .serializers import (
    ApplicationSerializer, InterviewSerializer, ApplicationNoteSerializer,
    ApplicationAnswerMemorySerializer, ApplicationQuestionSerializer
)
from resumes.models import ResumeVersion
from applications.services.state_machine import ApplicationStateMachine
from applications.services.preparation_service import ApplicationPreparationService
from applications.services.policy_evaluator import AutomationPolicyEvaluator
from applications.services.form_intelligence import FormIntelligenceService
from .serializers import (
    ApplicationSerializer, InterviewSerializer, ApplicationNoteSerializer,
    ApplicationAnswerMemorySerializer, ApplicationQuestionSerializer, FormSessionSerializer
)

class ApplicationViewSet(viewsets.ModelViewSet):
    """CRUD for user applications."""
    serializer_class = ApplicationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Application.objects.filter(user=self.request.user).order_by('-updated_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    @action(detail=True, methods=['post'])
    def prepare(self, request, pk=None):
        """Prepare application for submission, trigger readiness checks."""
        application = self.get_object()
        resume_version_id = request.data.get('resume_version_id')
        resume_version = None
        if resume_version_id:
            resume_version = get_object_or_404(ResumeVersion, pk=resume_version_id, user=request.user)
            
        try:
            readiness = ApplicationPreparationService.prepare_application(application, request.user, resume_version)
            
            # Policy Decision Phase 5B
            decision = AutomationPolicyEvaluator.evaluate(application)
            
            application.refresh_from_db()
            serializer = self.get_serializer(application)
            return Response({
                'application': serializer.data,
                'readiness': readiness,
                'policy_decision': {
                    'decision': decision.decision,
                    'reason_codes': decision.reason_codes
                }
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def transition(self, request, pk=None):
        """Manual status transition via state machine."""
        application = self.get_object()
        new_status = request.data.get('status')
        reason = request.data.get('reason', '')
        source = request.data.get('source', 'USER')
        
        try:
            ApplicationStateMachine.transition(application, new_status, source, reason)
            application.refresh_from_db()
            serializer = self.get_serializer(application)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def form_session(self, request, pk=None):
        """Initialize an Autofill Session."""
        application = self.get_object()
        provider = request.data.get('provider', 'UNKNOWN')
        url = request.data.get('url', '')
        
        session = FormIntelligenceService.initialize_session(request.user, application.id, provider, url)
        serializer = FormSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def analyze_form(self, request, pk=None):
        """Analyze DOM fields from the extension and return a safe autofill schema."""
        application = self.get_object()
        session_id = request.data.get('session_id')
        fields_data = request.data.get('fields', [])
        raw_schema = request.data.get('raw_schema', {})
        
        from .models import FormSession
        session = get_object_or_404(FormSession, id=session_id, application=application, user=request.user)
        
        detected_form = FormIntelligenceService.process_form_schema(session, fields_data, raw_schema)
        session.refresh_from_db()
        serializer = FormSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def record_autofill(self, request, pk=None):
        """Record autofill audit events from the extension."""
        application = self.get_object()
        session_id = request.data.get('session_id')
        action_name = request.data.get('action')
        field_key = request.data.get('field_key')
        
        from .models import FormSession
        session = get_object_or_404(FormSession, id=session_id, application=application, user=request.user)
        
        FormIntelligenceService.record_autofill_action(session, field_key, action_name)
        return Response({'status': 'recorded'}, status=status.HTTP_200_OK)

    # ==========================================
    # PHASE 5D - CONTROLLED EXECUTION DOMAIN
    # ==========================================
    
    @action(detail=True, methods=['get'])
    def execution(self, request, pk=None):
        application = self.get_object()
        from .models import ApplicationExecution
        from .serializers import ApplicationExecutionSerializer
        executions = ApplicationExecution.objects.filter(application=application, user=request.user).order_by('-created_at')
        if not executions.exists():
            return Response({'status': 'No execution history'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ApplicationExecutionSerializer(executions.first())
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def execution_validate(self, request, pk=None):
        application = self.get_object()
        snapshot_fingerprint = request.data.get('snapshot_fingerprint')
        
        from applications.services.execution_domain import PreExecutionValidationService
        is_valid, blocker, error_code = PreExecutionValidationService.validate_for_execution(
            request.user, application, snapshot_fingerprint
        )
        return Response({
            'is_valid': is_valid,
            'blocker_reason': blocker,
            'error_code': error_code
        })

    @action(detail=True, methods=['post'])
    def execution_create(self, request, pk=None):
        application = self.get_object()
        idempotency_key = request.data.get('idempotency_key')
        
        from applications.services.execution_domain import ExecutionReservationService
        from .serializers import ApplicationExecutionSerializer
        success, execution, error_code = ExecutionReservationService.reserve_execution_slot(
            request.user, application, idempotency_key
        )
        if not success:
            return Response({'error': error_code}, status=status.HTTP_400_BAD_REQUEST)
            
        serializer = ApplicationExecutionSerializer(execution)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def execution_confirm(self, request, pk=None):
        application = self.get_object()
        execution_id = request.data.get('execution_id')
        evidence = request.data.get('evidence', {})
        
        from .models import ApplicationExecution
        from applications.services.execution_domain import SubmissionVerificationService, ApplicationExecutionStateMachine
        from applications.constants import ExecutionStatus
        
        execution = get_object_or_404(ApplicationExecution, id=execution_id, application=application, user=request.user)
        
        receipt = SubmissionVerificationService.verify_receipt(execution, execution.provider, evidence)
        if receipt:
            ApplicationExecutionStateMachine.transition(execution, ExecutionStatus.SUCCEEDED)
            from .serializers import SubmissionReceiptSerializer
            return Response(SubmissionReceiptSerializer(receipt).data)
            
        ApplicationExecutionStateMachine.transition(execution, ExecutionStatus.UNKNOWN_RESULT)
        return Response({'status': 'UNKNOWN_RESULT', 'message': 'Evidence insufficient'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def execution_cancel(self, request, pk=None):
        application = self.get_object()
        execution_id = request.data.get('execution_id')
        
        from .models import ApplicationExecution
        from applications.services.execution_domain import ApplicationExecutionStateMachine
        from applications.constants import ExecutionStatus
        
        execution = get_object_or_404(ApplicationExecution, id=execution_id, application=application, user=request.user)
        try:
            ApplicationExecutionStateMachine.transition(execution, ExecutionStatus.CANCELLED)
            return Response({'status': 'cancelled'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def reconcile(self, request, pk=None):
        application = self.get_object()
        execution_id = request.data.get('execution_id')
        user_confirmed = request.data.get('user_confirmed', False)
        
        from .models import ApplicationExecution
        from applications.services.execution_domain import ReconciliationService
        from .serializers import SubmissionReceiptSerializer
        
        execution = get_object_or_404(ApplicationExecution, id=execution_id, application=application, user=request.user)
        
        success, result = ReconciliationService.reconcile_unknown(execution, user_confirmed)
        if not success:
            return Response({'error': result}, status=status.HTTP_400_BAD_REQUEST)
            
        if result: # Receipt created
            return Response(SubmissionReceiptSerializer(result).data)
        return Response({'status': 'reconciled_failed'})

class ApplicationQuestionViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationQuestionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return ApplicationQuestion.objects.filter(application__user=self.request.user)

class ApplicationAnswerMemoryViewSet(viewsets.ModelViewSet):
    """CRUD for user's reusable application answers."""
    serializer_class = ApplicationAnswerMemorySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return ApplicationAnswerMemory.objects.filter(user=self.request.user).order_by('-updated_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class InterviewViewSet(viewsets.ModelViewSet):
    """CRUD for interviews linked to an application."""
    serializer_class = InterviewSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Interview.objects.filter(application__user=self.request.user).order_by('scheduled_at')

    def perform_create(self, serializer):
        app_id = self.request.data.get('application')
        application = get_object_or_404(Application, pk=app_id, user=self.request.user)
        serializer.save(application=application)


class ApplicationNoteViewSet(viewsets.ModelViewSet):
    """CRUD for notes attached to applications."""
    serializer_class = ApplicationNoteSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return ApplicationNote.objects.filter(application__user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        app_id = self.request.data.get('application')
        application = get_object_or_404(Application, pk=app_id, user=self.request.user)
        serializer.save(application=application)


class AnalyticsView(views.APIView):
    """Provide high-level stats for the dashboard."""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user_apps = Application.objects.filter(user=request.user)
        total_apps = user_apps.count()
        status_qs = user_apps.values('status').annotate(cnt=Count('status'))
        status_breakdown = {item['status']: item['cnt'] for item in status_qs}
        avg_match = user_apps.aggregate(avg=Avg('match_score'))['avg'] or 0
        data = {
            'total_applications': total_apps,
            'status_breakdown': status_breakdown,
            'average_match_score': round(avg_match, 2),
        }
        return Response(data, status=status.HTTP_200_OK)
