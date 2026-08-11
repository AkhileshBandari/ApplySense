from rest_framework import serializers

class AnalyticsFilterSerializer(serializers.Serializer):
    time_range = serializers.CharField(required=False, default='30_DAYS')
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    country = serializers.CharField(required=False, allow_null=True)
    source = serializers.CharField(required=False, allow_null=True)
    provider = serializers.CharField(required=False, allow_null=True)
