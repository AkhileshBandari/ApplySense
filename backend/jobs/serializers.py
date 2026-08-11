from rest_framework import serializers
from .models import Job, JobRequirement, JobMatch, SavedJob

class JobRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobRequirement
        fields = (
            'required_skills', 'preferred_skills', 'minimum_experience', 
            'education_requirements', 'responsibilities'
        )

class JobMatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobMatch
        fields = (
            'overall_score', 'eligibility', 'dimension_scores', 
            'missing_required', 'missing_preferred', 'candidate_preference_conflicts',
            'created_at'
        )

class JobSerializer(serializers.ModelSerializer):
    requirements = JobRequirementSerializer(source='requirements_norm', read_only=True)
    match_info = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = (
            'id', 'title', 'company', 'location', 'work_mode', 'employment_type',
            'portal_type', 'source_url', 'application_url', 'description', 
            'requirements', 'salary_min', 'salary_max', 'salary_currency', 
            'salary_period', 'experience_min', 'experience_max', 'seniority',
            'industry', 'department', 'status', 'posted_at', 'last_seen_at',
            'match_info', 'is_saved'
        )
        
    def get_match_info(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        matches = obj.matches.all()
        if matches:
            return JobMatchSerializer(matches[0]).data
        return None
        
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return len(obj.savers.all()) > 0
