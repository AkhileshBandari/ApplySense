from rest_framework import serializers
from .models import (
    InterviewPlan, InterviewPlanSection, MockInterviewSession,
    InterviewQuestion, InterviewResponse, InterviewResponseEvaluation,
    InterviewWeakness, InterviewImprovementPlan
)

class InterviewPlanSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewPlanSection
        fields = '__all__'

class InterviewPlanSerializer(serializers.ModelSerializer):
    sections = InterviewPlanSectionSerializer(many=True, read_only=True)
    
    class Meta:
        model = InterviewPlan
        fields = '__all__'
        read_only_fields = ('user', 'context_snapshot', 'plan_version')

class InterviewQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewQuestion
        fields = '__all__'
        read_only_fields = ('session', 'plan', 'source_refs', 'expected_concepts')

class InterviewResponseEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewResponseEvaluation
        fields = '__all__'
        read_only_fields = ('relevance_score', 'completeness_score', 'technical_accuracy_score', 'structure_score', 'evidence_score', 'communication_score', 'overall_score', 'strengths', 'weaknesses', 'missing_concepts', 'unsupported_claims', 'evaluation_version')

class InterviewResponseSerializer(serializers.ModelSerializer):
    evaluation = InterviewResponseEvaluationSerializer(read_only=True)
    
    class Meta:
        model = InterviewResponse
        fields = '__all__'
        read_only_fields = ('user', 'evaluation_status')

class MockInterviewSessionSerializer(serializers.ModelSerializer):
    questions = InterviewQuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = MockInterviewSession
        fields = '__all__'
        read_only_fields = ('user', 'status', 'started_at', 'completed_at', 'duration_seconds', 'context_snapshot', 'overall_readiness_score')

class InterviewWeaknessSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewWeakness
        fields = '__all__'
        read_only_fields = ('user', 'session', 'severity', 'evidence', 'status')

class InterviewImprovementPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewImprovementPlan
        fields = '__all__'
        read_only_fields = ('user', 'session', 'structured_content')
