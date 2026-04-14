from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils.timezone import now
from django.db.models import Sum, Count
from datetime import timedelta
from transactions.models import Transaction
from django.contrib.auth import get_user_model
from .serializers import UserCountSerializer, RevenueSerializer
from payments.models import Subscription



User = get_user_model()
permission_classes = [IsAdminUser]

@api_view(['GET'])
def user_statistics(request):
    total_users = User.objects.count()
    premium_users = User.objects.filter(is_premium=True).count()

    data = {
        "total_users": total_users,
        "premium_users": premium_users,
    }
    serializer = UserCountSerializer(data)
    return Response(serializer.data)

@api_view(['GET'])
def revenue_statistics(request):
    total_revenue = Transaction.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    current_month = now().month
    monthly_revenue = Transaction.objects.filter(
        created_at__month=current_month
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    data = {
        "total_revenue": total_revenue,
        "monthly_revenue": monthly_revenue,
    }
    serializer = RevenueSerializer(data)
    return Response(serializer.data)

@api_view(['GET'])
def activity_logs(request):
    logs = ActivityLog.objects.all().order_by('-timestamp')[:50]
    serializer = ActivityLogSerializer(logs, many=True)
    return Response(serializer.data)
