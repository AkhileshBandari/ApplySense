from rest_framework import serializers
from career_integration.models import (
    CareerOperatingState, CareerDomainState, CareerIntegrationSnapshot, CareerOutcomeEvent,
    UserActionItem
)

class CareerDomainStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerDomainState
        fields = ['domain_name', 'status', 'last_synced_at']

class CareerOperatingStateSerializer(serializers.ModelSerializer):
    domains = CareerDomainStateSerializer(many=True, read_only=True)
    
    class Meta:
        model = CareerOperatingState
        fields = [
            'id', 'overall_readiness_score', 'current_primary_goal', 'top_blocker',
            'execution_velocity_score', 'application_momentum_score', 'current_os_state', 'overall_health',
            'domains', 'updated_at'
        ]

class UserActionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActionItem
        fields = '__all__'

class CareerIntegrationSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerIntegrationSnapshot
        fields = ['id', 'payload', 'snapshot_hash', 'trust_level_map', 'created_at']

class CareerOutcomeEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerOutcomeEvent
        fields = ['id', 'event_type', 'source_domain', 'payload', 'timestamp']
