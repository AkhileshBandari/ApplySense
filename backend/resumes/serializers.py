from rest_framework import serializers
from .models import Resume

class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ('id', 'file', 'file_name', 'parsed_text', 'health_score', 'ats_score', 'parsed_data', 'uploaded_at')
        read_only_fields = ('id', 'file_name', 'parsed_text', 'health_score', 'ats_score', 'parsed_data', 'uploaded_at')
