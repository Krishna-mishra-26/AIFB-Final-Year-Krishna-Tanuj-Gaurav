from rest_framework import serializers
from django.contrib.auth import get_user_model
from transactions.models import Transaction
from payments.models import Subscription
from analytics.models import ActivityLog

User = get_user_model()

class UserCountSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    premium_users = serializers.IntegerField()

class RevenueSerializer(serializers.Serializer):
    total_revenue = serializers.FloatField()
    monthly_revenue = serializers.FloatField()

class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = '__all__'
