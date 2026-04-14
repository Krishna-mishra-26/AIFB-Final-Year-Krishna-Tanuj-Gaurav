from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from insights.utils import get_spending_insights, predict_future_spending, suggest_savings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import SavingsGoal
from insights.utils import track_savings_progress
from django.db.models import Sum
from .models import BudgetInsight
from transactions.models import Budget, BudgetHistory
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from django.utils.timezone import now
from datetime import datetime, timedelta
from django.db.models import Sum
from rest_framework import status

from notifications.models import Notification
from django.utils.timezone import now
from .serializers import BudgetInsightSerializer

@login_required
def spending_insights_view(request):
    """API to get spending insights."""
    insights = get_spending_insights(request.user)
    return JsonResponse({"spending_insights": insights}, safe=False)

@login_required
def forecast_spending_view(request, category):
    """API to predict future spending for a given category."""
    forecast = predict_future_spending(request.user, category)
    return JsonResponse({"forecasted_spending": forecast})

@login_required
def savings_suggestions_view(request):
    """API to provide cost-saving recommendations."""
    suggestions = suggest_savings(request.user)
    return JsonResponse({"savings_recommendations": suggestions})



@csrf_exempt
@login_required
def add_savings_goal(request):
    """API to create a new savings goal."""
    if request.method == "POST":
        data = json.loads(request.body)
        goal = SavingsGoal.objects.create(
            user=request.user,
            goal_name=data["goal_name"],
            target_amount=data["target_amount"],
            deadline=datetime.strptime(data["deadline"], "%Y-%m-%d").date()
        )
        return JsonResponse({"message": "Goal created successfully!", "goal_id": goal.id})

@login_required
def get_savings_progress(request):
    """API to fetch user's savings goals and progress."""
    track_savings_progress(request.user)  # Auto-update progress
    goals = SavingsGoal.objects.filter(user=request.user).values()
    return JsonResponse({"goals": list(goals)}, safe=False)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_goal_savings(request):
    """API to manually update savings for a goal."""
    user = request.user
    goal_id = request.data.get("goal_id")
    saved_amount = request.data.get("saved_amount")

    try:
        goal = SavingsGoal.objects.get(id=goal_id, user=user)
        goal.saved_amount = saved_amount
        goal.save()

        # Check if goal is completed
        if goal.saved_amount >= goal.target_amount:
            Notifications.objects.create(
                user=user,
                message=f"🎉 Congratulations! You have completed your savings goal: {goal.goal_name}",
                created_at=now(),
                is_read=False
            )

        return Response({"message": "Goal updated successfully."})
    except SavingsGoal.DoesNotExist:
        return Response({"error": "Goal not found."}, status=404)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_insights(request):
    """
    Generates AI insights based on budget history and spending patterns.
    """
    user = request.user
    last_30_days = now() - timedelta(days=30)

    insights = []

    # Fetch spending trends from transactions
    spending_data = (
        Transaction.objects.filter(user_id=user.id, date__gte=last_30_days)
        .values('category_id')
        .annotate(total_spent=Sum('amount'))
    )

    # Fetch historical budget data
    budget_history = BudgetHistory.objects.filter(user=user).values(
        'category', 'previous_limit', 'actual_spent', 'suggested_limit'
    )

    # Generate AI insights based on history
    for record in budget_history:
        category = record['category']
        prev_limit = record['previous_limit']
        spent = record['actual_spent']
        suggested = record['suggested_limit']

        if spent > prev_limit:
            insights.append({
                "title": f"Overspending in {category}",
                "message": f"You spent ₹{spent}, exceeding your ₹{prev_limit} budget.",
                "suggested_budget": suggested,
                "category": category,
                "action_url": "#"
            })
        else:
            insights.append({
                "title": f"Good Budget Control in {category}",
                "message": f"You stayed within your ₹{prev_limit} budget. Suggested new budget: ₹{suggested}",
                "suggested_budget": suggested,
                "category": category,
                "action_url": "#"
            })

    return Response(insights)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_suggested_budget(request):
    """
    Updates the user's budget with the AI-suggested limit.
    """
    user = request.user
    category = request.data.get("category")
    new_limit = request.data.get("new_limit")

    if not category or not new_limit:
        return Response({"error": "Missing category or new limit"}, status=400)

    budget, created = Budget.objects.get_or_create(user_id=user.id, category=category)
    budget.monthly_limit = new_limit
    budget.save()

    return Response({"message": f"Budget updated successfully for {category}!", "new_limit": new_limit})


class BudgetInsightView(generics.ListAPIView):
    serializer_class = BudgetInsightSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return InsightsBudgetInsight.objects.filter(user_id=self.kwargs['user_id'])



# 🚀 1️⃣ AI-Powered Smart Recommendations
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_savings_insights(request):
    """Fetch AI-based savings recommendations for the user."""
    user = request.user
    insights = InsightsBudgetInsight.objects.filter(user_id=user.id).order_by('-created_at')

    insights_list = [
        {
            "category": insight.category,
            "average_spending": float(insight.average_spending),
            "forecasted_spending": float(insight.forecasted_spending),
            "savings_recommendation": insight.savings_recommendation
        }
        for insight in insights
    ]

    return Response(insights_list, status=status.HTTP_200_OK)

# 🚀 2️⃣ Monthly Savings Projection Chart
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_savings_projections(request):
    """Fetch monthly savings projections based on past spending trends."""
    user = request.user
    current_year = now().year
    current_month = now().month

    # Fetch past budget history
    budget_history = (
        BudgetHistory.objects
        .filter(user=user, year=current_year)
        .values('month')
        .annotate(total_saved=Sum('suggested_limit'))
        .order_by('month')
    )

    # Fetch current budget limit for future projection
    future_budget = (
        TransactionsBudget.objects
        .filter(user=user)
        .aggregate(total_budget=Sum('monthly_limit'))
    )['total_budget'] or 0

    # Prepare projection data
    months = []
    savings_data = []

    for entry in budget_history:
        month_name = datetime(current_year, entry['month'], 1).strftime('%b')  # e.g., "Jan"
        months.append(month_name)
        savings_data.append(float(entry['total_saved']))

    # Forecast next 3 months
    for i in range(1, 4):
        future_month = (current_month + i) % 12 or 12
        future_month_name = datetime(current_year, future_month, 1).strftime('%b')

        # Assume savings grow based on current monthly budget allocation
        months.append(future_month_name)
        savings_data.append(savings_data[-1] + float(future_budget) if savings_data else float(future_budget))

    return Response({"months": months, "amounts": savings_data}, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_monthly_savings_history(request):
    """Fetch monthly savings history for the user."""
    user = request.user
    savings_history = (
        BudgetHistory.objects
        .filter(user=user)
        .values('month', 'year')
        .annotate(
            total_saved=Sum('suggested_limit'),
            actual_spent=Sum('actual_spent'),
            previous_limit=Sum('previous_limit')
        )
        .order_by('year', 'month')
    )

    history_list = [
        {
            "month": datetime(year=entry['year'], month=entry['month'], day=1).strftime('%b %Y'),
            "total_saved": float(entry['total_saved'] or 0),
            "actual_spent": float(entry['actual_spent'] or 0),
            "previous_limit": float(entry['previous_limit'] or 0),
        }
        for entry in savings_history
    ]

    return Response(history_list)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """Fetch unread notifications for the user."""
    user = request.user
    notifications = Notifications.objects.filter(user=user, is_read=False).order_by('-created_at')

    notifications_list = [
        {"id": n.id, "message": n.message, "created_at": n.created_at.strftime("%Y-%m-%d %H:%M:%S")}
        for n in notifications
    ]

    return Response(notifications_list)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notifications_read(request):
    """Mark all notifications as read."""
    user = request.user
    Notifications.objects.filter(user=user, is_read=False).update(is_read=True)
    return Response({"message": "Notifications marked as read."})
