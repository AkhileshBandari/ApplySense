from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from career_outcomes.models import CareerOutcomeRecord, CareerOutcomeSnapshot
from career_outcomes.serializers import CareerOutcomeRecordSerializer, CareerOutcomeSnapshotSerializer
from career_outcomes.services.funnel_analysis_service import FunnelAnalysisService
from career_outcomes.services.attribution_service import AttributionAnalysisService
from career_outcomes.services.recommendation_engine import RecommendationEngineService

class CareerOutcomeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only views for Career Outcomes to prevent arbitrary client creation.
    Events should flow from canonical execution modules to integration, then here.
    """
    serializer_class = CareerOutcomeRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CareerOutcomeRecord.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def funnel(self, request):
        funnel = FunnelAnalysisService.calculate_funnel(request.user)
        return Response(funnel)

    @action(detail=False, methods=['get'])
    def resume_performance(self, request):
        perf = AttributionAnalysisService.analyze_resume_performance(request.user)
        return Response(perf)

    @action(detail=False, methods=['get'])
    def match_performance(self, request):
        perf = AttributionAnalysisService.analyze_match_score_performance(request.user)
        return Response(perf)
        
    @action(detail=False, methods=['get'])
    def tailoring_performance(self, request):
        perf = AttributionAnalysisService.analyze_tailoring_performance(request.user)
        return Response(perf)

    @action(detail=False, methods=['get'])
    def market_performance(self, request):
        perf = AttributionAnalysisService.analyze_market_performance(request.user)
        return Response(perf)

    @action(detail=False, methods=['get'])
    def global_market(self, request):
        perf = AttributionAnalysisService.analyze_global_market(request.user)
        return Response(perf)
        
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        recs = RecommendationEngineService.generate_recommendations(request.user)
        return Response({"recommendations": recs})

class CareerOutcomeSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CareerOutcomeSnapshotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CareerOutcomeSnapshot.objects.filter(user=self.request.user)
