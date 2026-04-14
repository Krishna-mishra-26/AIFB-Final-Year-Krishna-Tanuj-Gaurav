from django.urls import path
from insights.views import add_savings_goal, get_savings_progress, update_goal_savings
from .views import ai_insights
from .views import accept_suggested_budget,BudgetInsightView
from .views import get_savings_insights, get_savings_projections
from .views import get_monthly_savings_history
from .views import update_goal_savings, get_notifications, mark_notifications_read


urlpatterns = [
    path("add-goal/", add_savings_goal, name="add_savings_goal"),
    path("goal-progress/", get_savings_progress, name="get_savings_progress"),
    path('api/ai-insights/', ai_insights, name='ai-insights'),
    path('api/accept-suggested-budget/', accept_suggested_budget, name='accept-suggested-budget'),
    path('budget-insights/<uuid:user_id>/', BudgetInsightView.as_view(), name='budget-insights'),
    path('savings-insights/', get_savings_insights, name='savings_insights'),
    path('savings-projections/', get_savings_projections, name='savings_projections'),
    path('savings-history/', get_monthly_savings_history, name='savings_history'),
    path('update_goal_savings/', update_goal_savings, name='update_goal_savings'),
    path('notifications/', get_notifications, name='get_notifications'),
    path('mark-notifications-read/', mark_notifications_read, name='mark_notifications_read'),

]

