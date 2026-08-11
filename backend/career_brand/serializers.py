from rest_framework import serializers
from .models import (
    ProfessionalProfile,
    ProfessionalProfileSection,
    ProfessionalProfileAnalysis,
    ProfessionalProfileRecommendation,
    ProfessionalProfileVersion
)

class ProfessionalProfileSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionalProfileSection
        fields = ['id', 'section_type', 'position', 'raw_content', 'structured_content', 'source', 'verification_status', 'created_at', 'updated_at']
        read_only_fields = ['verification_status', 'created_at', 'updated_at']

class ProfessionalProfileSerializer(serializers.ModelSerializer):
    sections = ProfessionalProfileSectionSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProfessionalProfile
        fields = [
            'id', 'provider', 'external_profile_id', 'profile_url',
            'headline', 'about', 'location', 'industry', 'current_role', 'target_role',
            'source', 'sync_status', 'last_synced_at', 'created_at', 'updated_at',
            'sections'
        ]
        read_only_fields = ['sync_status', 'last_synced_at', 'created_at', 'updated_at']

class ProfessionalProfileRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionalProfileRecommendation
        fields = [
            'id', 'section_type', 'recommendation_type', 'severity', 'reason_code',
            'explanation', 'current_text', 'proposed_text', 'evidence_refs', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'section_type', 'recommendation_type', 'severity', 'reason_code',
            'explanation', 'current_text', 'evidence_refs', 'created_at', 'updated_at'
        ]

class ProfessionalProfileAnalysisSerializer(serializers.ModelSerializer):
    recommendations = ProfessionalProfileRecommendationSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProfessionalProfileAnalysis
        fields = [
            'id', 'target_role', 'target_job_id', 'overall_score', 'completeness_score',
            'evidence_alignment_score', 'keyword_alignment_score', 'consistency_score',
            'recruiter_readiness_score', 'analysis_version', 'snapshot', 'created_at',
            'recommendations'
        ]
        read_only_fields = [
            'overall_score', 'completeness_score', 'evidence_alignment_score',
            'keyword_alignment_score', 'consistency_score', 'recruiter_readiness_score',
            'analysis_version', 'snapshot', 'created_at'
        ]

class ProfessionalProfileVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionalProfileVersion
        fields = [
            'id', 'target_role', 'target_job_id', 'structured_content', 'source_analysis',
            'created_at'
        ]
        read_only_fields = ['structured_content', 'source_analysis', 'created_at']

