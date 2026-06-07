from rest_framework import serializers


class WhoopSummarySerializer(serializers.Serializer):
    connected = serializers.BooleanField()
    detail = serializers.CharField(required=False)
    snapshot_date = serializers.DateField(required=False)
    recovery_score = serializers.FloatField(required=False, allow_null=True)
    sleep_performance_percent = serializers.FloatField(required=False, allow_null=True)
    day_strain = serializers.FloatField(required=False, allow_null=True)
    hrv_rmssd_milli = serializers.FloatField(required=False, allow_null=True)
    resting_heart_rate = serializers.FloatField(required=False, allow_null=True)
    sleep_duration_minutes = serializers.IntegerField(required=False, allow_null=True)
    recent_workout_count = serializers.IntegerField(required=False)
    refreshed_at = serializers.DateTimeField(required=False)
