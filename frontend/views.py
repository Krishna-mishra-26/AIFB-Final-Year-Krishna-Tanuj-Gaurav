import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg, F
from datetime import datetime, timedelta
from users.models import User
from transactions.models import Transaction, Category
from group_expenses.models import Settlement
from insights.models import BudgetInsight, SavingsGoal
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import redirect


@login_required
def dashboard_stats(request):
    active_users = User.objects.filter(last_login__gte=datetime.now() - timedelta(days=30)).count()

    total_spending = BudgetInsight.objects.aggregate(Sum('average_spending'))['average_spending__sum'] or 1
    forecasted_spending = BudgetInsight.objects.aggregate(Sum('forecasted_spending'))['forecasted_spending__sum'] or 1
    accuracy_rate = round((forecasted_spending / total_spending) * 100, 2) if total_spending else 0

    total_settlements = Settlement.objects.filter(is_settled=True).count()
    total_transactions = Settlement.objects.count()
    support_availability = round((total_settlements / total_transactions) * 100, 2) if total_transactions else 0

    current_month = datetime.now().month
    monthly_savings = SavingsGoal.objects.filter(created_at__month=current_month).aggregate(Sum('saved_amount'))['saved_amount__sum'] or 0

    last_month_savings = SavingsGoal.objects.filter(created_at__month=current_month-1).aggregate(Sum('saved_amount'))['saved_amount__sum'] or 1
    savings_growth = round(((monthly_savings - last_month_savings) / last_month_savings) * 100, 2) if last_month_savings else 0

    investment_users = BudgetInsight.objects.values('user_id').distinct().count()
    investment_users_list = BudgetInsight.objects.values('user_id').distinct()[:5]  # Fetch 5 sample users

    average_roi = BudgetInsight.objects.aggregate(Avg('forecasted_spending'))['forecasted_spending__avg'] or 0

    context = {
        'active_users': active_users,
        'accuracy_rate': accuracy_rate,
        'support_availability': support_availability,
        'monthly_savings': monthly_savings,
        'savings_growth': savings_growth,
        'investment_users': investment_users,
        'investment_users_list': investment_users_list,
        'average_roi': average_roi,
    }

    return render(request, 'homepage.html', context)


@login_required
def financial_summary(request):
    user = request.user  

    today = datetime.today()
    current_month = today.month
    last_month = (today - timedelta(days=30)).month

    total_balance = Transaction.objects.filter(user=user).aggregate(Sum('amount'))['amount__sum'] or 0

    monthly_income = Transaction.objects.filter(user=user, amount__gt=0, date__month=current_month).aggregate(Sum('amount'))['amount__sum'] or 0

    monthly_expenses = Transaction.objects.filter(user=user, amount__lt=0, date__month=current_month).aggregate(Sum('amount'))['amount__sum'] or 0

    last_month_balance = Transaction.objects.filter(user=user, date__month=last_month).aggregate(Sum('amount'))['amount__sum'] or 1
    balance_change = round(((total_balance - last_month_balance) / last_month_balance) * 100, 2) if last_month_balance else 0

    last_month_income = Transaction.objects.filter(user=user, amount__gt=0, date__month=last_month).aggregate(Sum('amount'))['amount__sum'] or 1
    income_change = round(((monthly_income - last_month_income) / last_month_income) * 100, 2) if last_month_income else 0

    last_month_expenses = Transaction.objects.filter(user=user, amount__lt=0, date__month=last_month).aggregate(Sum('amount'))['amount__sum'] or 1
    expense_change = round(((monthly_expenses - last_month_expenses) / last_month_expenses) * 100, 2) if last_month_expenses else 0

    total_goal = SavingsGoal.objects.filter(user=user).aggregate(Sum('target_amount'))['target_amount__sum'] or 1
    total_savings = SavingsGoal.objects.filter(user=user).aggregate(Sum('saved_amount'))['saved_amount__sum'] or 0
    savings_progress = round((total_savings / total_goal) * 100, 2) if total_goal else 0

    context = {
        'total_balance': total_balance,
        'balance_change': balance_change,
        'monthly_income': monthly_income,
        'income_change': income_change,
        'monthly_expenses': monthly_expenses,
        'expense_change': expense_change,
        'savings_progress': savings_progress,
    }

    return render(request, 'dashboard.html', context) 





def spending_analysis(request):
    user_id = request.user.id  # Assuming user authentication
    period = request.GET.get('period', 'month')

    # Determine date range
    today = datetime.today().date()
    if period == 'week':
        start_date = today - timedelta(days=today.weekday())
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
    else:  # Default to month
        start_date = today.replace(day=1)

    transactions = Transaction.objects.filter(user_id=user_id, date__gte=start_date)

    # Group by date
    datewise_income = transactions.filter(category_type="income").values('date').annotate(total=Sum('amount'))
    datewise_expense = transactions.filter(category_type="expense").values('date').annotate(total=Sum('amount'))

    # Prepare chart data
    dates = [entry['date'].strftime('%Y-%m-%d') for entry in datewise_income]  # Convert date to string
    income = [entry['total'] for entry in datewise_income]
    expenses = [entry['total'] for entry in datewise_expense]

    # Expense category breakdown
    expense_categories = transactions.filter(category_type="expense").values('category_id').annotate(total=Sum('amount'))
    category_data = [
        {"category": Category.objects.get(id=entry["category_id"]).name, "amount": entry["total"]}
        for entry in expense_categories
    ]

    # Monthly expense trend
    monthly_expenses = transactions.filter(category_type="expense").extra({'month': "EXTRACT(MONTH FROM date)"}).values('month').annotate(total=Sum('amount'))
    months = [f"Month {entry['month']}" for entry in monthly_expenses]
    monthly_totals = [entry['total'] for entry in monthly_expenses]

    context = {
        "dates": dates,
        "income": income,
        "expenses": expenses,
        "expense_categories": category_data,
        "months": months,
        "monthly_expenses": monthly_totals,
    }

    return render(request, 'dashboard.html', {"context": json.dumps(context)})



