from rest_framework import serializers
from .models import CareerPath, CareerPathRequirement, CareerPathScenario, ScenarioAssumption

class CareerPathRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerPathRequirement
        fields = ['canonical_skill', 'skill_category', 'is_required', 'min_experience_months', 'market_demand_reference']

class CareerPathSerializer(serializers.ModelSerializer):
    requirements = CareerPathRequirementSerializer(many=True, read_only=True)
    class Meta:
        model = CareerPath
        fields = '__all__'

class ScenarioAssumptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScenarioAssumption
        fields = ['id', 'assumption_type', 'structured_data']
        read_only_fields = ['id']

class CareerPathScenarioSerializer(serializers.ModelSerializer):
    assumptions = ScenarioAssumptionSerializer(many=True, read_only=True)
    target_path = CareerPathSerializer(read_only=True)
    
    class Meta:
        model = CareerPathScenario
        fields = [
            'id', 'name', 'target_path', 'target_role', 'target_country',
            'target_region', 'work_mode', 'employment_type', 'status',
            'baseline_snapshot', 'simulated_snapshot', 'assumptions',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'baseline_snapshot', 'simulated_snapshot', 
            'created_at', 'updated_at'
        ]
