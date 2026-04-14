from rest_framework import serializers
from .models import BudgetInsight

class BudgetInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetInsight
        fields = '__all__'