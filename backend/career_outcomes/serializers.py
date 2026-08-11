from rest_framework import serializers
from career_outcomes.models import CareerOutcomeRecord, CareerOutcomeSnapshot

class CareerOutcomeRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerOutcomeRecord
        fields = '__all__'
        read_only_fields = ['user', 'confidence', 'normalized_state', 'detected_at']

class CareerOutcomeSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerOutcomeSnapshot
        fields = '__all__'
        read_only_fields = ['user', 'snapshot_hash', 'funnel_metrics', 'performance_metrics', 'comparison_groups', 'recommendation_inputs', 'confidence']
