from django.urls import path
from .views import (
    dashboard_stats, financial_summary, spending_analysis
)

urlpatterns = [
   
    path('dashboard-stats/', dashboard_stats, name='dashboard_stats'),
    path('financial-summary/', financial_summary, name='financial_summary'),
    path('spending-analysis/', spending_analysis, name='spending_analysis'),
    
]
