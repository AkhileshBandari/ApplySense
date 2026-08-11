from rest_framework import serializers
from career_decisions.models import CareerDecisionPlanVersion, CareerPriority, CareerAction

class CareerPrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerPriority
        fields = ['id', 'category', 'severity', 'impact_score', 'urgency', 'confidence', 'explanation', 'recommended_action']
        read_only_fields = fields

class CareerActionSerializer(serializers.ModelSerializer):
    dependencies = serializers.SerializerMethodField()
    
    class Meta:
        model = CareerAction
        fields = ['id', 'title', 'description', 'action_type', 'status', 'final_score', 'reason', 'dependencies']
        read_only_fields = ['id', 'title', 'description', 'action_type', 'final_score', 'reason', 'dependencies']
        
    def get_dependencies(self, obj):
        return [{"id": d.depends_on.id, "title": d.depends_on.title, "status": d.depends_on.status} for d in obj.dependencies.all()]

class CareerDecisionPlanVersionSerializer(serializers.ModelSerializer):
    priorities = CareerPrioritySerializer(many=True, read_only=True)
    actions = CareerActionSerializer(many=True, read_only=True)
    
    class Meta:
        model = CareerDecisionPlanVersion
        fields = ['id', 'generated_at', 'is_active', 'priorities', 'actions']
        read_only_fields = fields
