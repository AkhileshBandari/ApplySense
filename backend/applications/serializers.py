from rest_framework import serializers
from .models import (
    Application, Interview, ApplicationNote, 
    ApplicationStatusHistory, ApplicationQuestion, ApplicationAnswerMemory,
    PolicyDecision, FormSession, DetectedApplicationForm, DetectedApplicationFormField, FormSessionAuditLog,
    ApplicationExecution, SubmissionAttempt, SubmissionReceipt
)
from jobs.serializers import JobSerializer

class DetectedApplicationFormFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetectedApplicationFormField
        fields = '__all__'
        read_only_fields = ('id', 'form')

class DetectedApplicationFormSerializer(serializers.ModelSerializer):
    fields = DetectedApplicationFormFieldSerializer(many=True, read_only=True)
    class Meta:
        model = DetectedApplicationForm
        fields = '__all__'
        read_only_fields = ('id', 'session', 'detected_at')

class FormSessionAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormSessionAuditLog
        fields = '__all__'
        read_only_fields = ('id', 'session', 'timestamp')

class FormSessionSerializer(serializers.ModelSerializer):
    detected_form = DetectedApplicationFormSerializer(read_only=True)
    audit_logs = FormSessionAuditLogSerializer(many=True, read_only=True)
    class Meta:
        model = FormSession
        fields = '__all__'
        read_only_fields = ('id', 'user', 'application', 'started_at', 'updated_at')


class PolicyDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyDecision
        fields = '__all__'
        read_only_fields = ('id', 'application', 'timestamp')

class InterviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = '__all__'
        read_only_fields = ('id', 'application')

class ApplicationNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationNote
        fields = '__all__'
        read_only_fields = ('id', 'application', 'created_at')

class ApplicationStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationStatusHistory
        fields = '__all__'
        read_only_fields = ('id', 'application', 'timestamp')

class ApplicationQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationQuestion
        fields = '__all__'
        read_only_fields = ('id', 'application', 'created_at', 'updated_at')

class ApplicationAnswerMemorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationAnswerMemory
        fields = '__all__'
        read_only_fields = ('id', 'user', 'created_at', 'updated_at', 'last_used_at')

class ApplicationSerializer(serializers.ModelSerializer):
    job_details = JobSerializer(source='job', read_only=True)
    interviews = InterviewSerializer(many=True, read_only=True)
    notes = ApplicationNoteSerializer(many=True, read_only=True)
    questions = ApplicationQuestionSerializer(many=True, read_only=True)
    status_history = ApplicationStatusHistorySerializer(many=True, read_only=True)
    policy_decisions = PolicyDecisionSerializer(many=True, read_only=True)

    class Meta:
        model = Application
        fields = (
            'id', 'user', 'job', 'job_details', 'company', 'role', 'source', 
            'application_provider', 'application_mode', 'resume_version',
            'snapshot', 'status', 'preparation_status', 'submission_status',
            'application_url', 'external_identifier', 'match_score', 'match_details',
            'applied_at', 'prepared_at', 'submitted_at', 'last_status_change_at',
            'created_at', 'updated_at', 'interviews', 'notes', 'questions', 'status_history', 'policy_decisions'
        )
        read_only_fields = ('id', 'user', 'snapshot', 'created_at', 'updated_at', 'last_status_change_at', 'prepared_at', 'submitted_at')


class SubmissionAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionAttempt
        fields = '__all__'
        read_only_fields = ('id', 'execution', 'started_at', 'completed_at')

class SubmissionReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionReceipt
        fields = '__all__'
        read_only_fields = ('id', 'application', 'execution', 'created_at')

class ApplicationExecutionSerializer(serializers.ModelSerializer):
    attempts = SubmissionAttemptSerializer(many=True, read_only=True)
    receipts = SubmissionReceiptSerializer(many=True, read_only=True)
    
    class Meta:
        model = ApplicationExecution
        fields = '__all__'
        read_only_fields = ('id', 'user', 'application', 'created_at', 'updated_at')
