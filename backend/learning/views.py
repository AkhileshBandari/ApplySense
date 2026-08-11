from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from learning.models import (
    SkillGapAnalysis, SkillGapItem, LearningRoadmap, LearningRoadmapItem,
    ProjectRecommendation, TargetType
)
from learning.services.gap_analysis import SkillGapAnalysisService
from learning.services.roadmap import LearningRoadmapService
from learning.services.projects import ProjectRecommendationService
from learning.services.progress import LearningProgressService

# ----------------------------------------------------------------------
# Serializers
# ----------------------------------------------------------------------

class SkillGapItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillGapItem
        fields = '__all__'

class SkillGapAnalysisSerializer(serializers.ModelSerializer):
    gap_items = SkillGapItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = SkillGapAnalysis
        fields = '__all__'

class LearningRoadmapItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningRoadmapItem
        fields = '__all__'

class LearningRoadmapSerializer(serializers.ModelSerializer):
    items = LearningRoadmapItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = LearningRoadmap
        fields = '__all__'

class ProjectRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectRecommendation
        fields = '__all__'

# ----------------------------------------------------------------------
# Views
# ----------------------------------------------------------------------

class GapAnalysisViewSet(viewsets.ModelViewSet):
    serializer_class = SkillGapAnalysisSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SkillGapAnalysis.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        target_type = request.data.get('target_type')
        
        if target_type == TargetType.SPECIFIC_JOB:
            job_id = request.data.get('job_id')
            if not job_id:
                return Response({"error": "job_id required"}, status=status.HTTP_400_BAD_REQUEST)
            analysis = SkillGapAnalysisService.generate_analysis_for_job(request.user, job_id)
            
        elif target_type in [TargetType.TARGET_ROLE, TargetType.MARKET_AGGREGATE]:
            target_role = request.data.get('target_role')
            country_code = request.data.get('country_code', '')
            if not target_role:
                return Response({"error": "target_role required"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                analysis = SkillGapAnalysisService.generate_analysis_for_role(request.user, target_role, country_code)
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Invalid target_type"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(analysis)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class LearningRoadmapViewSet(viewsets.ModelViewSet):
    serializer_class = LearningRoadmapSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LearningRoadmap.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        analysis_id = request.data.get('analysis_id')
        hours_per_week = request.data.get('hours_per_week', 10)
        
        try:
            analysis = SkillGapAnalysis.objects.get(id=analysis_id, user=request.user)
        except SkillGapAnalysis.DoesNotExist:
            return Response({"error": "Analysis not found"}, status=status.HTTP_404_NOT_FOUND)
            
        roadmap = LearningRoadmapService.generate_roadmap(analysis, int(hours_per_week))
        serializer = self.get_serializer(roadmap)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class LearningRoadmapItemViewSet(viewsets.ModelViewSet):
    serializer_class = LearningRoadmapItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LearningRoadmapItem.objects.filter(roadmap__user=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        item = self.get_object()
        new_status = request.data.get('status')
        if new_status:
            LearningProgressService.mark_item_status(item, new_status)
        return super().partial_update(request, *args, **kwargs)

class ProjectRecommendationViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectRecommendationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectRecommendation.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        analysis_id = request.data.get('analysis_id')
        try:
            analysis = SkillGapAnalysis.objects.get(id=analysis_id, user=request.user)
        except SkillGapAnalysis.DoesNotExist:
            return Response({"error": "Analysis not found"}, status=status.HTTP_404_NOT_FOUND)
            
        recs = ProjectRecommendationService.generate_recommendations(analysis)
        serializer = self.get_serializer(recs, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
