from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import AnalyticsFilterSerializer

from .services.kpi_service import get_overview_kpis
from .services.funnel_service import get_funnel_analytics
from .services.timeline_service import get_trends_analytics
from .services.performance_service import (
    get_sources_analytics, get_providers_analytics, 
    get_resumes_analytics, get_markets_analytics
)
from .services.automation_service import get_automation_analytics
from .services.insight_engine import generate_insights

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def overview_analytics(request):
    serializer = AnalyticsFilterSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    return Response(get_overview_kpis(request.user, serializer.validated_data))

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def funnel_analytics(request):
    serializer = AnalyticsFilterSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    return Response(get_funnel_analytics(request.user, serializer.validated_data))

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trends_analytics(request):
    serializer = AnalyticsFilterSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    return Response(get_trends_analytics(request.user, serializer.validated_data))

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sources_analytics(request):
    serializer = AnalyticsFilterSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    return Response(get_sources_analytics(request.user, serializer.validated_data))

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def providers_analytics(request):
    serializer = AnalyticsFilterSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    return Response(get_providers_analytics(request.user, serializer.validated_data))

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def resumes_analytics(request):
    serializer = AnalyticsFilterSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    return Response(get_resumes_analytics(request.user, serializer.validated_data))

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def markets_analytics(request):
    serializer = AnalyticsFilterSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    return Response(get_markets_analytics(request.user, serializer.validated_data))

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def automation_analytics(request):
    serializer = AnalyticsFilterSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    return Response(get_automation_analytics(request.user, serializer.validated_data))

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def insights_analytics(request):
    serializer = AnalyticsFilterSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    return Response(generate_insights(request.user, serializer.validated_data))
