from rest_framework import serializers
from career_execution.models import CareerExecutionPlan, CareerExecutionItem, CareerExecutionProgress, CareerExecutionDependency

class CareerExecutionDependencySerializer(serializers.ModelSerializer):
    depends_on_title = serializers.CharField(source='depends_on.title', read_only=True)
    depends_on_status = serializers.CharField(source='depends_on.status', read_only=True)
    
    class Meta:
        model = CareerExecutionDependency
        fields = ['id', 'depends_on', 'depends_on_title', 'depends_on_status']

class CareerExecutionItemSerializer(serializers.ModelSerializer):
    dependencies = CareerExecutionDependencySerializer(many=True, read_only=True)
    
    class Meta:
        model = CareerExecutionItem
        fields = [
            'id', 'title', 'description', 'action_type', 'source_phase',
            'status', 'execution_mode', 'impact_score', 'urgency_score',
            'effort_penalty', 'final_score', 'reason', 'created_at',
            'completed_at', 'dependencies'
        ]

class CareerExecutionProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerExecutionProgress
        fields = [
            'overall_score', 'skill_score', 'evidence_score', 'brand_score',
            'interview_score', 'application_score', 'pathway_score', 'timestamp'
        ]

class CareerExecutionPlanSerializer(serializers.ModelSerializer):
    items = CareerExecutionItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = CareerExecutionPlan
        fields = ['id', 'created_at', 'updated_at', 'items']
