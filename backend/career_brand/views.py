from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import (
    ProfessionalProfile,
    ProfessionalProfileAnalysis,
    ProfessionalProfileRecommendation,
    ProfessionalProfileVersion
)
from .serializers import (
    ProfessionalProfileSerializer,
    ProfessionalProfileAnalysisSerializer,
    ProfessionalProfileRecommendationSerializer,
    ProfessionalProfileVersionSerializer
)
from .services.ProfileOptimizationService import ProfileOptimizationService
from .services.ClaimValidationService import ClaimValidationService

class ProfessionalProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfessionalProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ProfessionalProfile.objects.filter(user=self.request.user)
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        profile = self.get_object()
        analysis = ProfileOptimizationService.analyze_profile(request.user, profile)
        return Response(ProfessionalProfileAnalysisSerializer(analysis).data)
        
    @action(detail=True, methods=['post'])
    def approve_version(self, request, pk=None):
        profile = self.get_object()
        # In full app: extract content to JSON and save as version
        version = ProfessionalProfileVersion.objects.create(
            user=request.user,
            profile=profile,
            target_role=profile.target_role,
            structured_content={'headline': profile.headline, 'about': profile.about}
        )
        return Response(ProfessionalProfileVersionSerializer(version).data)

class ProfessionalProfileAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProfessionalProfileAnalysisSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ProfessionalProfileAnalysis.objects.filter(user=self.request.user)

class ProfessionalProfileRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProfessionalProfileRecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ProfessionalProfileRecommendation.objects.filter(analysis__user=self.request.user)
        
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        rec = self.get_object()
        # Mocking proposal generation via ProfileOptimizationService
        proposal = ProfileOptimizationService.generate_headline_proposal(request.user, "Target Role")
        
        if proposal is None:
            return Response({'error': 'AI generated unsupported claims. Please try again.'}, status=400)
            
        rec.proposed_text = proposal
        rec.save()
        return Response(self.get_serializer(rec).data)
        
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        rec = self.get_object()
        rec.status = 'ACCEPTED'
        rec.save()
        return Response(self.get_serializer(rec).data)

    @action(detail=True, methods=['post'])
    def edit(self, request, pk=None):
        rec = self.get_object()
        new_text = request.data.get('proposed_text', '')
        
        # Validating user edit!
        validation = ClaimValidationService.validate_generated_proposal(request.user, new_text)
        if not validation['is_safe']:
            return Response({'error': validation['rejection_reason']}, status=400)
            
        rec.proposed_text = new_text
        rec.status = 'EDITED'
        rec.save()
        return Response(self.get_serializer(rec).data)

class ProfessionalProfileVersionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProfessionalProfileVersionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ProfessionalProfileVersion.objects.filter(user=self.request.user)

