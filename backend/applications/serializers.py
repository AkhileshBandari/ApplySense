from rest_framework import serializers
from .models import Application, Interview, ApplicationNote
from jobs.serializers import JobSerializer

class InterviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = '__all__'
        read_only_fields = ('id', 'application')

class ApplicationNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationNote
        fields = '__all__'
        read_only_fields = ('id', 'application')

class ApplicationSerializer(serializers.ModelSerializer):
    job_details = JobSerializer(source='job', read_only=True)
    interviews = InterviewSerializer(many=True, read_only=True)
    notes = ApplicationNoteSerializer(many=True, read_only=True)

    class Meta:
        model = Application
        fields = ('id', 'job', 'job_details', 'status', 'match_score', 
                  'match_details', 'applied_at', 'created_at', 'updated_at', 
                  'interviews', 'notes')
        read_only_fields = ('id', 'created_at', 'updated_at')
