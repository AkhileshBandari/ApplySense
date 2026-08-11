from rest_framework import serializers
from evidence.models import (
    GitHubConnection, GitHubSyncRun, CandidateRepository, CandidateSkillEvidence,
    PortfolioConnection, PortfolioProject
)

class GitHubConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitHubConnection
        # Never serialize _encrypted_access_token
        exclude = ['_encrypted_access_token']
        read_only_fields = ['user', 'connected_at', 'last_synced_at', 'sync_status', 'sync_error_code', 'sync_error_message', 'created_at', 'updated_at']

class GitHubSyncRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitHubSyncRun
        fields = '__all__'
        read_only_fields = ['user', 'connection']

class CandidateRepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateRepository
        exclude = ['raw_metadata_snapshot'] # Don't send huge raw metadata to frontend
        read_only_fields = ['user', 'github_connection']

class CandidateSkillEvidenceSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill_taxonomy.canonical_name', read_only=True)
    repository_name = serializers.CharField(source='repository.name', read_only=True)
    portfolio_project_title = serializers.CharField(source='portfolio_project.title', read_only=True)
    
    class Meta:
        model = CandidateSkillEvidence
        fields = '__all__'
        read_only_fields = ['user', 'skill_taxonomy', 'source_type', 'repository', 'portfolio_project', 'evidence_type', 'first_observed_at', 'created_at', 'updated_at']

class PortfolioConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioConnection
        fields = '__all__'
        read_only_fields = ['user', 'status', 'last_analyzed_at', 'analysis_status', 'error_code', 'error_message', 'created_at', 'updated_at']

class PortfolioProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioProject
        exclude = ['evidence_snapshot']
        read_only_fields = ['user', 'portfolio', 'first_observed_at', 'created_at', 'updated_at']
