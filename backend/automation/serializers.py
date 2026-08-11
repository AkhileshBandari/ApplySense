from rest_framework import serializers
from automation.models import AutoApplyConfiguration, AutoApplyRun, UserActionRequired

class AutoApplyConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutoApplyConfiguration
        fields = [
            'auto_apply_enabled',
            'daily_application_limit',
            'weekly_application_limit',
            'target_roles',
            'excluded_roles',
            'target_locations',
            'minimum_salary',
            'salary_currency',
            'require_tailored_resume',
            'allow_unknown_salary',
            'allow_unknown_company',
            'allow_external_ats'
        ]

class AutoApplyRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutoApplyRun
        fields = '__all__'

class UserActionRequiredSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActionRequired
        fields = '__all__'
