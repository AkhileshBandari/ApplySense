from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from evidence.models import (
    GitHubConnection, GitHubSyncRun, CandidateRepository, CandidateSkillEvidence,
    PortfolioConnection, PortfolioProject
)
from evidence.serializers import (
    GitHubConnectionSerializer, CandidateRepositorySerializer, CandidateSkillEvidenceSerializer,
    PortfolioConnectionSerializer
)
from evidence.services.github_service import GitHubRepositoryAnalysisService, CandidateEvidenceAggregationService
from evidence.services.portfolio_service import PortfolioAnalysisService
from profiles.models import Skill, VerificationStatus
from profiles.services.candidate_context import CandidateContextService

class GitHubConnectionViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = GitHubConnectionSerializer

    def get_queryset(self):
        return GitHubConnection.objects.filter(user=self.request.user)
        
    def perform_create(self, serializer):
        # Prevent multiple connections per user
        if GitHubConnection.objects.filter(user=self.request.user).exists():
            GitHubConnection.objects.filter(user=self.request.user).delete()
        connection = serializer.save(user=self.request.user)
        
        # We can accept an optional raw token from the request in a secure POST payload
        raw_token = self.request.data.get('access_token')
        if raw_token:
            connection.set_token(raw_token)
            connection.save()

    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        connection = self.get_object()
        
        # Run sync synchronously for this implementation, normally would use Celery
        sync_run = GitHubRepositoryAnalysisService.sync_user_repositories(connection)
        
        if sync_run.status == 'COMPLETED':
            return Response({'status': 'Sync completed successfully', 'repositories_discovered': sync_run.repositories_discovered}, status=status.HTTP_200_OK)
        else:
            return Response({'status': sync_run.status, 'error': sync_run.error_message}, status=status.HTTP_400_BAD_REQUEST)

class CandidateRepositoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CandidateRepositorySerializer

    def get_queryset(self):
        return CandidateRepository.objects.filter(user=self.request.user).order_by('-stars')

class CandidateSkillEvidenceViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CandidateSkillEvidenceSerializer

    def get_queryset(self):
        return CandidateSkillEvidence.objects.filter(user=self.request.user).select_related('skill_taxonomy', 'repository')

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """
        Accept or Reject evidence.
        Accepting it passes it into the Candidate verification workflow.
        """
        evidence = self.get_object()
        action_type = request.data.get('action') # ACCEPT or REJECT
        
        if action_type == 'ACCEPT':
            evidence.status = 'ACCEPTED'
            evidence.save()
            
            # Integrate with Phase 1-2 Profile CandidateContext workflow!
            # Do NOT bypass verification. It inserts as UNVERIFIED if it's new.
            profile = request.user.profile
            skill_name = evidence.skill_taxonomy.canonical_name
            
            existing_skill = Skill.objects.filter(profile=profile, name__iexact=skill_name).first()
            if not existing_skill:
                # Add it, but ONLY as UNVERIFIED, relying on the source being EXTERNAL_IMPORTED.
                Skill.objects.create(
                    profile=profile,
                    name=skill_name,
                    source='EXTERNAL_IMPORTED',
                    verification_status=VerificationStatus.UNVERIFIED
                )
            
            return Response({'status': 'Evidence accepted and sent to candidate context.'})
            
        elif action_type == 'REJECT':
            evidence.status = 'REJECTED'
            evidence.save()
            return Response({'status': 'Evidence rejected.'})
            
        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

class EvidenceSummaryViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        summary = CandidateEvidenceAggregationService.get_user_evidence_summary(request.user)
        return Response(summary)

class PortfolioConnectionViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PortfolioConnectionSerializer

    def get_queryset(self):
        return PortfolioConnection.objects.filter(user=self.request.user)
        
    def perform_create(self, serializer):
        if PortfolioConnection.objects.filter(user=self.request.user).exists():
            PortfolioConnection.objects.filter(user=self.request.user).delete()
        serializer.save(user=self.request.user, normalized_url=serializer.validated_data.get('portfolio_url'))

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        connection = self.get_object()
        PortfolioAnalysisService.analyze_portfolio(connection)
        
        if connection.analysis_status == 'COMPLETED':
            return Response({'status': 'Analysis completed successfully'})
        else:
            return Response({'status': connection.analysis_status, 'error': connection.error_message}, status=status.HTTP_400_BAD_REQUEST)
