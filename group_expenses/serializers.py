from rest_framework import serializers
from .models import Group, GroupExpense, GroupMember, Settlement


from rest_framework import serializers
from .models import Group, GroupExpense, GroupMember, Settlement

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'created_at']

class GroupExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupExpense
        fields = ['id', 'group', 'user', 'description', 'category', 'amount', 'created_at']

class GroupMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMember
        fields = ['id', 'group', 'user', 'joined_at']

class SettlementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settlement
        fields = ['id', 'group', 'payer', 'payee', 'amount', 'razorpay_payment_id', 'is_settled', 'settled_at']
