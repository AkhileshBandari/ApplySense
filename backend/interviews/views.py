from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import InterviewPlan, MockInterviewSession, InterviewQuestion, InterviewResponse, InterviewResponseEvaluation, InterviewWeakness, InterviewImprovementPlan
from .serializers import (
    InterviewPlanSerializer, MockInterviewSessionSerializer, InterviewQuestionSerializer,
    InterviewResponseSerializer, InterviewWeaknessSerializer, InterviewImprovementPlanSerializer
)
from .services.InterviewPlanService import InterviewPlanService
from .services.InterviewQuestionGenerationService import InterviewQuestionGenerationService
from .services.Evaluators import STARResponseEvaluator, TechnicalResponseEvaluator
from .services.AdaptiveFollowUpService import AdaptiveFollowUpService
from .services.AnalyticsServices import InterviewReadinessService, InterviewWeaknessService, InterviewImprovementPlanService
from jobs.models import Job

class InterviewPlanViewSet(viewsets.ModelViewSet):
    serializer_class = InterviewPlanSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return InterviewPlan.objects.filter(user=self.request.user)
        
    @action(detail=False, methods=['post'])
    def generate(self, request):
        job_id = request.data.get('job_id')
        interview_type = request.data.get('interview_type', 'GENERAL')
        difficulty = request.data.get('difficulty', 'INTERMEDIATE')
        target_role = request.data.get('target_role')
        
        job = Job.objects.filter(id=job_id).first() if job_id else None
        
        plan = InterviewPlanService.generate_plan(
            user=request.user,
            job=job,
            target_role=target_role,
            interview_type=interview_type,
            difficulty=difficulty
        )
        
        return Response(InterviewPlanSerializer(plan).data, status=status.HTTP_201_CREATED)

class MockInterviewSessionViewSet(viewsets.ModelViewSet):
    serializer_class = MockInterviewSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return MockInterviewSession.objects.filter(user=self.request.user)
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        session = self.get_object()
        if session.status != 'CREATED':
            return Response({'error': 'Session already started'}, status=status.HTTP_400_BAD_REQUEST)
            
        session.status = 'IN_PROGRESS'
        session.save()
        
        # Generate initial questions if none exist
        if not session.questions.exists():
            generator = InterviewQuestionGenerationService()
            for section in session.plan.sections.all():
                generator.generate_questions(session, section, count=2)
                
        return Response(MockInterviewSessionSerializer(session).data)
        
    @action(detail=True, methods=['post'])
    def answer(self, request, pk=None):
        session = self.get_object()
        if session.status != 'IN_PROGRESS':
            return Response({'error': 'Session is not in progress'}, status=status.HTTP_400_BAD_REQUEST)
            
        question_id = request.data.get('question_id')
        response_text = request.data.get('response_text')
        
        if not question_id or not response_text:
            return Response({'error': 'question_id and response_text required'}, status=status.HTTP_400_BAD_REQUEST)
            
        question = InterviewQuestion.objects.filter(id=question_id, session=session).first()
        if not question:
            return Response({'error': 'Invalid question_id'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Create response
        resp = InterviewResponse.objects.create(
            question=question,
            user=request.user,
            response_text=response_text
        )
        
        # Evaluate
        evaluator = STARResponseEvaluator() if question.question_type == 'BEHAVIORAL' else TechnicalResponseEvaluator()
        eval_data = evaluator.evaluate(resp)
        
        evaluation = InterviewResponseEvaluation.objects.create(
            response=resp,
            **{k:v for k,v in eval_data.items() if hasattr(InterviewResponseEvaluation, k)}
        )
        
        # Generate Follow Up
        follow_up_service = AdaptiveFollowUpService()
        follow_up_q = follow_up_service.generate_follow_up(evaluation)
        
        return Response({
            'evaluation': eval_data,
            'follow_up_question': InterviewQuestionSerializer(follow_up_q).data if follow_up_q else None
        })

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        session = self.get_object()
        if session.status != 'IN_PROGRESS':
            return Response({'error': 'Session is not in progress'}, status=status.HTTP_400_BAD_REQUEST)
            
        session.status = 'COMPLETED'
        
        # Extract Weaknesses
        InterviewWeaknessService.extract_weaknesses(session)
        # Generate Improvement Plan
        InterviewImprovementPlanService.generate_plan(session)
        
        # Calculate session score based on evaluations
        evals = InterviewResponseEvaluation.objects.filter(response__question__session=session)
        if evals.exists():
            avg = sum(e.overall_score for e in evals if e.overall_score is not None) / evals.count()
            session.overall_readiness_score = int(avg)
            
        session.save()
        return Response(MockInterviewSessionSerializer(session).data)

    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        session = self.get_object()
        weaknesses = InterviewWeakness.objects.filter(session=session)
        plan = InterviewImprovementPlan.objects.filter(session=session).first()
        
        return Response({
            'session': MockInterviewSessionSerializer(session).data,
            'weaknesses': InterviewWeaknessSerializer(weaknesses, many=True).data,
            'improvement_plan': InterviewImprovementPlanSerializer(plan).data if plan else None
        })

class InterviewAnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def readiness(self, request):
        readiness = InterviewReadinessService.calculate_readiness(request.user)
        return Response({'readiness_score': readiness})
        
    @action(detail=False, methods=['get'])
    def weaknesses(self, request):
        weaknesses = InterviewWeakness.objects.filter(user=request.user)
        return Response(InterviewWeaknessSerializer(weaknesses, many=True).data)
