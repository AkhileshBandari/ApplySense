from rest_framework import serializers
from .models import Resume, ResumeAnalysis, ResumeVersion, TailoringChange

class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ('id', 'file', 'file_name', 'status', 'parsed_text', 'health_score', 'ats_score', 'parsed_data', 'uploaded_at')
        read_only_fields = ('id', 'file_name', 'status', 'parsed_text', 'health_score', 'ats_score', 'parsed_data', 'uploaded_at')

class ResumeAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeAnalysis
        fields = '__all__'

class TailoringChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TailoringChange
        fields = '__all__'

class ResumeVersionSerializer(serializers.ModelSerializer):
    changes = TailoringChangeSerializer(many=True, read_only=True)
    class Meta:
        model = ResumeVersion
        fields = '__all__'
