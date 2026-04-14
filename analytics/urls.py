from django.urls import path
from .views import user_statistics, revenue_statistics, activity_logs

urlpatterns = [
    path('user-stats/', user_statistics, name='user_statistics'),
    path('revenue-stats/', revenue_statistics, name='revenue_statistics'),
    path('activity-logs/', activity_logs, name='activity_logs'),
]
