from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Profile, FinancialData

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields =  '__all__'
class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'phone_number']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user





class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'

class FinancialDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialData
        fields = '__all__'
