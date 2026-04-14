import re
import json
import calendar
from decimal import Decimal, InvalidOperation
from datetime import date
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from group_expenses.models import Group, GroupExpense, GroupMember
from insights.models import SavingsGoal
from payments.models import RecurringPayment
from transactions.models import Budget, Category, Transaction, alerts

User = get_user_model()


def _build_unique_username(seed_value: str) -> str:
    """Generate a unique username from a human-readable seed."""
    base = re.sub(r"[^a-zA-Z0-9_]", "", seed_value.replace(" ", "").lower())
    if not base:
        base = "user"

    candidate = base[:150]
    counter = 1
    while User.objects.filter(username=candidate).exists():
        suffix = f"_{counter}"
        candidate = f"{base[: max(1, 150 - len(suffix))]}{suffix}"
        counter += 1

    return candidate


def _common_context(user):
    unread_alerts_count = alerts.objects.filter(user=user, is_read=False).count()
    recent_alerts = alerts.objects.filter(user=user).order_by("-created_at")[:5]
    return {
        "unread_alerts_count": unread_alerts_count,
        "recent_alerts": recent_alerts,
    }


def _build_context(user, page_context):
    context = _common_context(user)
    context.update(page_context)
    return context


def _next_due_date(current_due_date, frequency):
    if frequency == "daily":
        return current_due_date + timedelta(days=1)
    if frequency == "weekly":
        return current_due_date + timedelta(days=7)
    if frequency == "yearly":
        return current_due_date + timedelta(days=365)
    return current_due_date + timedelta(days=30)


def _create_due_alerts(user, today):
    due_soon = RecurringPayment.objects.filter(
        user=user,
        status="active",
        next_payment_date__lte=today + timedelta(days=2),
    )
    for payment in due_soon:
        if payment.next_payment_date < today:
            alert_message = f"Recurring payment '{payment.name}' is overdue."
        elif payment.next_payment_date == today:
            alert_message = f"Recurring payment '{payment.name}' is due today."
        else:
            alert_message = f"Recurring payment '{payment.name}' is due in {(payment.next_payment_date - today).days} day(s)."

        exists_today = alerts.objects.filter(
            user=user,
            message=alert_message,
            created_at__date=today,
        ).exists()
        if not exists_today:
            alerts.objects.create(user=user, message=alert_message)


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard_page")
    return render(request, "public/home.html")


@login_required
def dashboard_page(request):
    user_transactions = Transaction.objects.filter(user=request.user)
    user_budgets = Budget.objects.filter(user=request.user)
    user_goals = SavingsGoal.objects.filter(user=request.user)
    user_recurring = RecurringPayment.objects.filter(user=request.user)

    today = date.today()
    total_income = (
        user_transactions.filter(category_type__iexact="income").aggregate(total=Sum("amount"))["total"] or 0
    )
    total_expenses = (
        user_transactions.filter(category_type__iexact="expense").aggregate(total=Sum("amount"))["total"] or 0
    )
    total_balance = total_income - total_expenses
    monthly_income = (
        user_transactions.filter(date__year=today.year, date__month=today.month, category_type__iexact="income")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )
    monthly_expenses = (
        user_transactions.filter(date__year=today.year, date__month=today.month, category_type__iexact="expense")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )
    monthly_savings = monthly_income - monthly_expenses
    saved_total = SavingsGoal.objects.filter(user=request.user).aggregate(total=Sum("saved_amount"))["total"] or 0
    active_budgets = Budget.objects.filter(user=request.user).count()
    upcoming_recurring_qs = RecurringPayment.objects.filter(
        user=request.user,
        status="active",
        next_payment_date__gte=today,
    ).order_by("next_payment_date")
    upcoming_recurring_count = upcoming_recurring_qs.count()

    savings_ratio_percent = 0
    expense_pressure_percent = 0
    if monthly_income > 0:
        savings_ratio_percent = int(max(0, min(100, (monthly_savings / monthly_income) * 100)))
        expense_pressure_percent = int(max(0, min(100, (monthly_expenses / monthly_income) * 100)))

    if savings_ratio_percent >= 30:
        savings_label = "Good"
    elif savings_ratio_percent >= 10:
        savings_label = "Moderate"
    else:
        savings_label = "Needs Attention"

    if expense_pressure_percent >= 90:
        pressure_label = "High"
    elif expense_pressure_percent >= 70:
        pressure_label = "Moderate"
    else:
        pressure_label = "Low"

    last_30_days_start = today - timedelta(days=29)
    recent_30_day_income = (
        user_transactions.filter(date__gte=last_30_days_start, category_type__iexact="income").aggregate(total=Sum("amount"))["total"]
        or Decimal("0")
    )
    recent_30_day_expense = (
        user_transactions.filter(date__gte=last_30_days_start, category_type__iexact="expense").aggregate(total=Sum("amount"))["total"]
        or Decimal("0")
    )
    active_days = max(1, min(30, (today - last_30_days_start).days + 1))
    average_daily_income = recent_30_day_income / Decimal(active_days)
    average_daily_expense = recent_30_day_expense / Decimal(active_days)

    days_remaining = Decimal(calendar.monthrange(today.year, today.month)[1] - today.day)
    projected_income = monthly_income + (average_daily_income * days_remaining)
    projected_expenses = monthly_expenses + (average_daily_expense * days_remaining)
    projected_balance = projected_income - projected_expenses

    last_7_start = today - timedelta(days=6)
    prev_7_start = today - timedelta(days=13)
    prev_7_end = today - timedelta(days=7)
    last_7_expenses = (
        user_transactions.filter(date__gte=last_7_start, date__lte=today, category_type__iexact="expense")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )
    prev_7_expenses = (
        user_transactions.filter(date__gte=prev_7_start, date__lte=prev_7_end, category_type__iexact="expense")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )
    spending_spike_ratio = (
        float(last_7_expenses / prev_7_expenses)
        if prev_7_expenses
        else (2.0 if last_7_expenses > 0 else 1.0)
    )

    ai_risk_score = 20
    if spending_spike_ratio >= 1.5:
        ai_risk_score += 30
    elif spending_spike_ratio >= 1.2:
        ai_risk_score += 15
    if projected_balance < total_balance:
        ai_risk_score += 25
    if expense_pressure_percent >= 80:
        ai_risk_score += 15
    if not user_budgets.exists():
        ai_risk_score += 10
    ai_risk_score = int(max(0, min(100, ai_risk_score)))

    if ai_risk_score >= 75:
        ai_risk_label = "High Risk"
    elif ai_risk_score >= 45:
        ai_risk_label = "Moderate Risk"
    else:
        ai_risk_label = "Healthy"

    recent_transactions = (
        Transaction.objects.filter(user=request.user)
        .select_related("category")
        .order_by("-date", "-created_at")[:5]
    )

    last_30_days_start = today - timedelta(days=29)
    trend_transactions = (
        Transaction.objects.filter(user=request.user, date__gte=last_30_days_start)
        .order_by("date", "id")
        .values("date", "amount", "category_type")
    )
    trend_map = {}
    for entry in trend_transactions:
        key = entry["date"].isoformat()
        if key not in trend_map:
            trend_map[key] = {"income": Decimal("0"), "expense": Decimal("0")}
        trend_map[key][entry["category_type"]] += entry["amount"]

    trend_labels = []
    trend_income = []
    trend_expense = []
    for offset in range(30):
        current_day = last_30_days_start + timedelta(days=offset)
        day_key = current_day.isoformat()
        trend_labels.append(current_day.strftime("%d %b"))
        day_values = trend_map.get(day_key, {"income": Decimal("0"), "expense": Decimal("0")})
        trend_income.append(float(day_values["income"]))
        trend_expense.append(float(day_values["expense"]))

    month_expense_categories = (
        Transaction.objects.filter(
            user=request.user,
            category_type__iexact="expense",
            date__year=today.year,
            date__month=today.month,
        )
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")[:5]
    )
    category_labels = [row["category__name"] or "General" for row in month_expense_categories]
    category_values = [float(row["total"] or 0) for row in month_expense_categories]

    budget_cards = []
    for budget in user_budgets.order_by("category"):
        spent = (
            Transaction.objects.filter(
                user=request.user,
                category__name__iexact=budget.category,
                category_type__iexact="expense",
                date__year=today.year,
                date__month=today.month,
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0")
        )
        percent_used = 0
        if budget.monthly_limit > 0:
            percent_used = int(min(100, max(0, (spent / budget.monthly_limit) * 100)))
        budget_cards.append(
            {
                "category": budget.category,
                "monthly_limit": budget.monthly_limit,
                "spent": spent,
                "remaining": budget.monthly_limit - spent,
                "percent_used": percent_used,
            }
        )

    category_alerts = []
    for budget in budget_cards:
        if budget["percent_used"] >= 90:
            category_alerts.append(f"{budget['category']} is nearly exhausted at {budget['percent_used']}% usage.")
        elif budget["percent_used"] >= 75:
            category_alerts.append(f"{budget['category']} is moving quickly at {budget['percent_used']}% usage.")

    ai_insights = []
    ai_insights.append(f"Expected month-end balance is Rs {float(projected_balance):.2f}.")
    if spending_spike_ratio >= 1.5:
        ai_insights.append(f"Expense activity in the last 7 days is {spending_spike_ratio:.1f}x the previous week.")
    else:
        ai_insights.append("Recent spending is stable compared with the previous week.")
    if category_alerts:
        ai_insights.extend(category_alerts[:2])
    else:
        ai_insights.append("No category is under immediate pressure right now.")
    if upcoming_recurring_count:
        ai_insights.append(f"{upcoming_recurring_count} recurring payment(s) are scheduled ahead.")

    goal_cards = []
    for goal in user_goals.order_by("deadline")[:4]:
        target = goal.target_amount or Decimal("0")
        saved = goal.saved_amount or Decimal("0")
        progress_percent = int(min(100, max(0, (saved / target) * 100))) if target > 0 else 0
        goal_cards.append(
            {
                "goal_name": goal.goal_name,
                "progress_percent": progress_percent,
                "saved_amount": saved,
                "target_amount": target,
                "deadline": goal.deadline,
                "status": goal.status,
            }
        )

    recurring_cards = []
    for payment in user_recurring.filter(status="active").order_by("next_payment_date")[:4]:
        days_left = (payment.next_payment_date - today).days
        recurring_cards.append(
            {
                "name": payment.name,
                "amount": payment.amount,
                "next_payment_date": payment.next_payment_date,
                "days_left": days_left,
            }
        )

    latest_alerts = alerts.objects.filter(user=request.user).order_by("-created_at")[:4]

    action_items = []
    if monthly_expenses > monthly_income and monthly_income > 0:
        action_items.append("Expenses are above income this month. Review categories with the highest spend.")
    if not budget_cards:
        action_items.append("Create a few budgets to unlock burn-rate tracking.")
    if due_this_week := RecurringPayment.objects.filter(user=request.user, status="active", next_payment_date__lte=today + timedelta(days=7)).count():
        action_items.append(f"You have {due_this_week} recurring payment(s) due within 7 days.")
    if not goal_cards:
        action_items.append("Add at least one savings goal to track financial progress.")

    context = _build_context(request.user, {
        "active_page": "dashboard",
        "total_balance": total_balance,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "monthly_savings": monthly_savings,
        "saved_total": saved_total,
        "active_budgets": active_budgets,
        "upcoming_recurring_count": upcoming_recurring_count,
        "savings_ratio_percent": savings_ratio_percent,
        "expense_pressure_percent": expense_pressure_percent,
        "savings_label": savings_label,
        "pressure_label": pressure_label,
        "ai_risk_score": ai_risk_score,
        "ai_risk_label": ai_risk_label,
        "projected_balance": projected_balance,
        "projected_income": projected_income,
        "projected_expenses": projected_expenses,
        "ai_insights": ai_insights,
        "trend_labels_data": trend_labels,
        "trend_income_data": trend_income,
        "trend_expense_data": trend_expense,
        "category_labels_data": category_labels,
        "category_values_data": category_values,
        "recent_transactions": recent_transactions,
        "upcoming_recurring": upcoming_recurring_qs[:5],
        "trend_labels_json": json.dumps(trend_labels),
        "trend_income_json": json.dumps(trend_income),
        "trend_expense_json": json.dumps(trend_expense),
        "category_labels_json": json.dumps(category_labels),
        "category_values_json": json.dumps(category_values),
        "budget_cards": budget_cards,
        "goal_cards": goal_cards,
        "recurring_cards": recurring_cards,
        "latest_alerts": latest_alerts,
        "action_items": action_items,
    })
    return render(request, "public/dashboard.html", context)


@login_required
def transactions_page(request):
    if request.method == "POST":
        action = request.POST.get("action", "create")
        if action == "delete":
            transaction_id = request.POST.get("transaction_id")
            deleted, _ = Transaction.objects.filter(id=transaction_id, user=request.user).delete()
            if deleted:
                messages.success(request, "Transaction deleted.")
            else:
                messages.error(request, "Transaction not found.")
            return redirect("transactions_page")

        category_name = request.POST.get("category", "General").strip() or "General"
        category_type = request.POST.get("category_type", "expense").strip().lower()
        amount = request.POST.get("amount", "").strip()
        date_value = request.POST.get("date")
        description = request.POST.get("description", "").strip()

        if category_type not in {"income", "expense"}:
            category_type = "expense"

        try:
            parsed_amount = Decimal(amount)
        except (InvalidOperation, TypeError):
            parsed_amount = None

        if parsed_amount is not None and parsed_amount > 0 and date_value:
            category_obj, _ = Category.objects.get_or_create(
                user=request.user,
                name=category_name,
            )
            Transaction.objects.create(
                user=request.user,
                amount=parsed_amount,
                category=category_obj,
                category_type=category_type,
                description=description,
                date=date_value,
            )
            messages.success(request, "Transaction added successfully.")
            return redirect("transactions_page")

        messages.error(request, "Please enter a valid amount and date.")

    filtered_transactions = Transaction.objects.filter(user=request.user).select_related("category")

    search_query = request.GET.get("q", "").strip()
    filter_type = request.GET.get("type", "").strip().lower()
    filter_category = request.GET.get("category", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    if search_query:
        filtered_transactions = filtered_transactions.filter(description__icontains=search_query)
    if filter_type in {"income", "expense"}:
        filtered_transactions = filtered_transactions.filter(category_type=filter_type)
    if filter_category:
        filtered_transactions = filtered_transactions.filter(category__name__iexact=filter_category)
    if date_from:
        filtered_transactions = filtered_transactions.filter(date__gte=date_from)
    if date_to:
        filtered_transactions = filtered_transactions.filter(date__lte=date_to)

    transactions = filtered_transactions.order_by("-date", "-created_at")[:100]
    filtered_income = filtered_transactions.filter(category_type="income").aggregate(total=Sum("amount"))["total"] or 0
    filtered_expense = filtered_transactions.filter(category_type="expense").aggregate(total=Sum("amount"))["total"] or 0
    categories = (
        Category.objects.filter(user=request.user)
        .order_by("name")
        .values_list("name", flat=True)
        .distinct()
    )

    chart_start = date.today() - timedelta(days=13)
    trend_source = filtered_transactions.filter(date__gte=chart_start).order_by("date", "id")
    trend_map = {}
    for entry in trend_source.values("date", "amount", "category_type"):
        key = entry["date"].isoformat()
        if key not in trend_map:
            trend_map[key] = {"income": Decimal("0"), "expense": Decimal("0")}
        trend_map[key][entry["category_type"]] += entry["amount"]

    trend_labels = []
    trend_income = []
    trend_expense = []
    for offset in range(14):
        current_day = chart_start + timedelta(days=offset)
        day_key = current_day.isoformat()
        day_values = trend_map.get(day_key, {"income": Decimal("0"), "expense": Decimal("0")})
        trend_labels.append(current_day.strftime("%d %b"))
        trend_income.append(float(day_values["income"]))
        trend_expense.append(float(day_values["expense"]))

    category_summary = (
        filtered_transactions.filter(category_type__iexact="expense")
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")[:6]
    )
    category_labels = [row["category__name"] or "General" for row in category_summary]
    category_values = [float(row["total"] or 0) for row in category_summary]

    return render(
        request,
        "public/transactions.html",
        _build_context(request.user, {
            "active_page": "transactions",
            "transactions": transactions,
            "today": date.today(),
            "filter_q": search_query,
            "filter_type": filter_type,
            "filter_category": filter_category,
            "filter_date_from": date_from,
            "filter_date_to": date_to,
            "categories": categories,
            "filtered_income": filtered_income,
            "filtered_expense": filtered_expense,
            "transaction_trend_labels_json": json.dumps(trend_labels),
            "transaction_trend_income_json": json.dumps(trend_income),
            "transaction_trend_expense_json": json.dumps(trend_expense),
            "transaction_category_labels_json": json.dumps(category_labels),
            "transaction_category_values_json": json.dumps(category_values),
        }),
    )


@login_required
def budget_page(request):
    if request.method == "POST":
        action = request.POST.get("action", "upsert")

        if action == "delete":
            budget_id = request.POST.get("budget_id")
            deleted, _ = Budget.objects.filter(id=budget_id, user=request.user).delete()
            if deleted:
                messages.success(request, "Budget deleted.")
            else:
                messages.error(request, "Budget not found.")
            return redirect("budget_page")

        category = request.POST.get("category", "").strip()
        monthly_limit = request.POST.get("monthly_limit", "").strip()

        try:
            parsed_limit = Decimal(monthly_limit)
        except (InvalidOperation, TypeError):
            parsed_limit = None

        if category and parsed_limit is not None and parsed_limit > 0:
            Budget.objects.update_or_create(
                user=request.user,
                category=category,
                defaults={"monthly_limit": parsed_limit},
            )
            messages.success(request, "Budget updated successfully.")
            return redirect("budget_page")

        messages.error(request, "Category and a valid monthly limit are required.")

    budgets = Budget.objects.filter(user=request.user).order_by("category")
    today = date.today()
    monthly_spend_qs = (
        Transaction.objects.filter(
            user=request.user,
            category_type__iexact="expense",
            date__year=today.year,
            date__month=today.month,
        )
        .values("category__name")
        .annotate(total=Sum("amount"))
    )
    spend_map = {row["category__name"]: row["total"] or Decimal("0") for row in monthly_spend_qs}

    budget_rows = []
    for budget in budgets:
        spent = spend_map.get(budget.category, Decimal("0"))
        remaining = budget.monthly_limit - spent
        usage_percent = 0
        if budget.monthly_limit > 0:
            usage_percent = min(100, max(0, int((spent / budget.monthly_limit) * 100)))

        budget_rows.append(
            {
                "id": budget.id,
                "category": budget.category,
                "monthly_limit": budget.monthly_limit,
                "created_at": budget.created_at,
                "spent": spent,
                "remaining": remaining,
                "usage_percent": usage_percent,
            }
        )

    budget_labels = [row["category"] for row in budget_rows]
    budget_limits = [float(row["monthly_limit"] or 0) for row in budget_rows]
    budget_spent = [float(row["spent"] or 0) for row in budget_rows]

    return render(
        request,
        "public/budget.html",
        _build_context(request.user, {
            "active_page": "budget",
            "budgets": budget_rows,
            "budget_labels_json": json.dumps(budget_labels),
            "budget_limits_json": json.dumps(budget_limits),
            "budget_spent_json": json.dumps(budget_spent),
        }),
    )


@login_required
def goals_page(request):
    if request.method == "POST":
        action = request.POST.get("action", "create")

        if action == "add_savings":
            goal_id = request.POST.get("goal_id")
            add_amount = request.POST.get("add_amount", "").strip()
            try:
                parsed_amount = Decimal(add_amount)
            except (InvalidOperation, TypeError):
                parsed_amount = None

            goal = SavingsGoal.objects.filter(id=goal_id, user=request.user).first()
            if not goal:
                messages.error(request, "Goal not found.")
                return redirect("goals_page")

            if parsed_amount is None or parsed_amount <= 0:
                messages.error(request, "Please enter a valid savings amount.")
                return redirect("goals_page")

            goal.saved_amount = (goal.saved_amount or Decimal("0")) + parsed_amount
            goal.update_progress()
            if goal.status != "Completed":
                goal.save(update_fields=["saved_amount"])
            messages.success(request, "Savings updated successfully.")
            return redirect("goals_page")

        if action == "delete":
            goal_id = request.POST.get("goal_id")
            deleted, _ = SavingsGoal.objects.filter(id=goal_id, user=request.user).delete()
            if deleted:
                messages.success(request, "Goal deleted.")
            else:
                messages.error(request, "Goal not found.")
            return redirect("goals_page")

        goal_name = request.POST.get("goal_name", "").strip()
        target_amount = request.POST.get("target_amount", "").strip()
        deadline = request.POST.get("deadline", "").strip()

        try:
            parsed_target = Decimal(target_amount)
        except (InvalidOperation, TypeError):
            parsed_target = None

        if goal_name and parsed_target is not None and parsed_target > 0 and deadline:
            SavingsGoal.objects.create(
                user=request.user,
                goal_name=goal_name,
                target_amount=parsed_target,
                deadline=deadline,
            )
            messages.success(request, "Savings goal created successfully.")
            return redirect("goals_page")

        messages.error(request, "Goal name, valid target amount, and deadline are required.")

    goals = SavingsGoal.objects.filter(user=request.user).order_by("deadline")
    today = date.today()
    goal_rows = []
    for goal in goals:
        target = goal.target_amount or Decimal("0")
        saved = goal.saved_amount or Decimal("0")
        progress_percent = int(min(100, max(0, (saved / target) * 100))) if target > 0 else 0
        days_left = (goal.deadline - today).days if goal.deadline else None
        overdue_days = abs(days_left) if days_left is not None and days_left < 0 else 0
        goal_rows.append(
            {
                "id": goal.id,
                "goal_name": goal.goal_name,
                "deadline": goal.deadline,
                "saved_amount": saved,
                "target_amount": target,
                "status": goal.status,
                "progress_percent": progress_percent,
                "days_left": days_left,
                "overdue_days": overdue_days,
            }
        )
    goal_labels = [row["goal_name"] for row in goal_rows[:6]]
    goal_saved = [float(row["saved_amount"] or 0) for row in goal_rows[:6]]
    goal_target = [float(row["target_amount"] or 0) for row in goal_rows[:6]]

    return render(
        request,
        "public/goals.html",
        _build_context(request.user, {
            "active_page": "goals",
            "goals": goal_rows,
            "goal_labels_json": json.dumps(goal_labels),
            "goal_saved_json": json.dumps(goal_saved),
            "goal_target_json": json.dumps(goal_target),
        }),
    )

@login_required
def group_expenses_page(request):
    if request.method == "POST":
        action = request.POST.get("action", "create_group")

        if action == "create_group":
            group_name = request.POST.get("group_name", "").strip()
            group_description = request.POST.get("group_description", "").strip()

            if not group_name:
                messages.error(request, "Group name is required.")
                return redirect("group_expenses_page")

            group = Group.objects.create(name=group_name, description=group_description)
            GroupMember.objects.get_or_create(group=group, user=request.user)
            messages.success(request, "Group created successfully.")
            return redirect(f"/group-expenses/?group={group.id}")

        if action == "add_member":
            group_id = request.POST.get("group_id")
            member_email = request.POST.get("member_email", "").strip().lower()

            group = Group.objects.filter(id=group_id).first()
            if not group:
                messages.error(request, "Group not found.")
                return redirect("group_expenses_page")

            if not GroupMember.objects.filter(group=group, user=request.user).exists():
                messages.error(request, "You are not a member of this group.")
                return redirect(f"/group-expenses/?group={group.id}")

            member_user = User.objects.filter(email=member_email).first()
            if not member_user:
                messages.error(request, "User with this email does not exist.")
                return redirect(f"/group-expenses/?group={group.id}")

            _, created = GroupMember.objects.get_or_create(group=group, user=member_user)
            if created:
                messages.success(request, "Member added successfully.")
            else:
                messages.info(request, "User is already in this group.")
            return redirect(f"/group-expenses/?group={group.id}")

        if action == "add_expense":
            group_id = request.POST.get("group_id")
            description = request.POST.get("description", "").strip()
            amount = request.POST.get("amount", "").strip()
            category = request.POST.get("category", "").strip() or "General"
            expense_date = request.POST.get("date")
            split_member_ids = request.POST.getlist("split_members")

            group = Group.objects.filter(id=group_id).first()
            if not group:
                messages.error(request, "Group not found.")
                return redirect("group_expenses_page")

            payer_member = GroupMember.objects.filter(group=group, user=request.user).first()
            if not payer_member:
                messages.error(request, "You are not a member of this group.")
                return redirect(f"/group-expenses/?group={group.id}")

            try:
                parsed_amount = Decimal(amount)
            except (InvalidOperation, TypeError):
                parsed_amount = None

            if not description or parsed_amount is None or parsed_amount <= 0 or not expense_date:
                messages.error(request, "Please provide valid expense details.")
                return redirect(f"/group-expenses/?group={group.id}")

            selected_members = GroupMember.objects.filter(group=group, id__in=split_member_ids)
            if not selected_members.exists():
                selected_members = GroupMember.objects.filter(group=group)

            member_count = selected_members.count() or 1
            split_amount = parsed_amount / Decimal(member_count)

            group_expense = GroupExpense.objects.create(
                description=description,
                amount=parsed_amount,
                category=category,
                date=expense_date,
                paid_by=payer_member,
                split_amount=split_amount,
            )
            group_expense.split_members.set(selected_members)
            messages.success(request, "Group expense added successfully.")
            return redirect(f"/group-expenses/?group={group.id}")

    membership_group_ids = GroupMember.objects.filter(user=request.user).values_list("group_id", flat=True)
    groups = Group.objects.filter(id__in=membership_group_ids).order_by("-created_at")
    selected_group_id = request.GET.get("group")
    selected_group = groups.filter(id=selected_group_id).first() if selected_group_id else groups.first()
    group_members = GroupMember.objects.filter(group=selected_group).select_related("user") if selected_group else []
    group_expenses = (
        GroupExpense.objects.filter(paid_by__group=selected_group)
        .select_related("paid_by", "paid_by__user")
        .prefetch_related("split_members", "split_members__user")
        .order_by("-date", "-id")
        if selected_group
        else []
    )

    settlement = {
        "you_paid": Decimal("0"),
        "you_owe": Decimal("0"),
        "you_are_owed": Decimal("0"),
        "net": Decimal("0"),
    }
    current_member = GroupMember.objects.filter(group=selected_group, user=request.user).first() if selected_group else None
    if current_member:
        for expense in group_expenses:
            members_count = expense.split_members.count() or 1
            per_member = expense.split_amount or (expense.amount / Decimal(members_count))

            if expense.paid_by_id == current_member.id:
                settlement["you_paid"] += expense.amount
                settlement["you_are_owed"] += per_member * Decimal(max(0, members_count - 1))
            elif expense.split_members.filter(id=current_member.id).exists():
                settlement["you_owe"] += per_member

        settlement["net"] = settlement["you_are_owed"] - settlement["you_owe"]

    expense_category_summary = []
    if selected_group:
        category_totals = {}
        for expense in group_expenses:
            category_name = expense.category or "General"
            category_totals[category_name] = category_totals.get(category_name, Decimal("0")) + (expense.amount or Decimal("0"))
        expense_category_summary = sorted(category_totals.items(), key=lambda item: item[1], reverse=True)

    expense_category_labels = [item[0] for item in expense_category_summary[:6]]
    expense_category_values = [float(item[1] or 0) for item in expense_category_summary[:6]]
    settlement_labels = ["You paid", "You owe", "You are owed", "Net position"]
    settlement_values = [
        float(settlement["you_paid"]),
        float(settlement["you_owe"]),
        float(settlement["you_are_owed"]),
        float(settlement["net"]),
    ]

    return render(
        request,
        "frontend/group_expenses.html",
        _build_context(request.user, {
            "active_page": "group_expenses",
            "groups": groups,
            "selected_group": selected_group,
            "group_members": group_members,
            "group_expenses": group_expenses,
            "settlement": settlement,
            "expense_category_labels_json": json.dumps(expense_category_labels),
            "expense_category_values_json": json.dumps(expense_category_values),
            "settlement_labels_json": json.dumps(settlement_labels),
            "settlement_values_json": json.dumps(settlement_values),
        }),
    )


@login_required
def recurring_page(request):
    today = date.today()
    _create_due_alerts(request.user, today)

    if request.method == "POST":
        action = request.POST.get("action", "create")

        if action == "update_status":
            payment_id = request.POST.get("payment_id")
            status = request.POST.get("status", "active")
            updated = RecurringPayment.objects.filter(id=payment_id, user=request.user).update(status=status)
            if updated:
                messages.success(request, "Recurring payment status updated.")
            else:
                messages.error(request, "Recurring payment not found.")
            return redirect("recurring_page")

        if action == "delete":
            payment_id = request.POST.get("payment_id")
            deleted, _ = RecurringPayment.objects.filter(id=payment_id, user=request.user).delete()
            if deleted:
                messages.success(request, "Recurring payment removed.")
            else:
                messages.error(request, "Recurring payment not found.")
            return redirect("recurring_page")

        if action == "mark_paid":
            payment_id = request.POST.get("payment_id")
            payment = RecurringPayment.objects.filter(id=payment_id, user=request.user).first()
            if not payment:
                messages.error(request, "Recurring payment not found.")
                return redirect("recurring_page")

            base_due_date = payment.next_payment_date if payment.next_payment_date > today else today
            payment.next_payment_date = _next_due_date(base_due_date, payment.frequency)
            payment.status = "active"
            payment.save(update_fields=["next_payment_date", "status", "updated_at"])
            messages.success(request, f"Marked '{payment.name}' as paid. Next due date updated.")
            return redirect("recurring_page")

        name = request.POST.get("name", "").strip()
        amount = request.POST.get("amount", "").strip()
        category = request.POST.get("category", "others").strip()
        frequency = request.POST.get("frequency", "monthly").strip()
        next_payment_date = request.POST.get("next_payment_date")

        try:
            parsed_amount = Decimal(amount)
        except (InvalidOperation, TypeError):
            parsed_amount = None

        valid_categories = {choice[0] for choice in RecurringPayment.CATEGORY_CHOICES}
        valid_frequencies = {choice[0] for choice in RecurringPayment.FREQUENCY_CHOICES}

        if category not in valid_categories:
            category = "others"
        if frequency not in valid_frequencies:
            frequency = "monthly"

        if name and parsed_amount is not None and parsed_amount > 0 and next_payment_date:
            RecurringPayment.objects.create(
                user=request.user,
                name=name,
                amount=parsed_amount,
                category=category,
                frequency=frequency,
                next_payment_date=next_payment_date,
                status="active",
            )
            messages.success(request, "Recurring payment added successfully.")
            return redirect("recurring_page")

        messages.error(request, "Please provide valid recurring payment details.")

    recurring_payments = list(RecurringPayment.objects.filter(user=request.user).order_by("next_payment_date"))
    for payment in recurring_payments:
        payment.days_left = (payment.next_payment_date - today).days
        payment.is_due_soon = payment.days_left <= 3
        payment.is_overdue = payment.days_left < 0

    monthly_recurring_total = (
        RecurringPayment.objects.filter(user=request.user, status="active", frequency="monthly")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )
    due_this_week_count = len([payment for payment in recurring_payments if 0 <= payment.days_left <= 7])
    recurring_status_counts = {
        "active": sum(1 for payment in recurring_payments if payment.status == "active"),
        "paused": sum(1 for payment in recurring_payments if payment.status == "paused"),
        "canceled": sum(1 for payment in recurring_payments if payment.status == "canceled"),
    }
    recurring_labels = [payment.name for payment in recurring_payments[:6]]
    recurring_days_left = [max(0, int(payment.days_left)) for payment in recurring_payments[:6]]

    return render(
        request,
        "public/recurring.html",
        _build_context(request.user, {
            "active_page": "recurring",
            "recurring_payments": recurring_payments,
            "recurring_categories": RecurringPayment.CATEGORY_CHOICES,
            "recurring_frequencies": RecurringPayment.FREQUENCY_CHOICES,
            "recurring_statuses": [("active", "Active"), ("paused", "Paused"), ("canceled", "Canceled")],
            "monthly_recurring_total": monthly_recurring_total,
            "due_this_week_count": due_this_week_count,
            "recurring_status_labels_json": json.dumps(["Active", "Paused", "Canceled"]),
            "recurring_status_values_json": json.dumps([
                recurring_status_counts["active"],
                recurring_status_counts["paused"],
                recurring_status_counts["canceled"],
            ]),
            "recurring_labels_json": json.dumps(recurring_labels),
            "recurring_days_left_json": json.dumps(recurring_days_left),
        }),
    )


@login_required
def notifications_page(request):
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "mark_all_read":
            alerts.objects.filter(user=request.user, is_read=False).update(is_read=True)
            messages.success(request, "All notifications marked as read.")
            return redirect("notifications_page")

        if action == "mark_read":
            alert_id = request.POST.get("alert_id")
            updated = alerts.objects.filter(id=alert_id, user=request.user).update(is_read=True)
            if updated:
                messages.success(request, "Notification marked as read.")
            else:
                messages.error(request, "Notification not found.")
            return redirect("notifications_page")

    alert_rows = alerts.objects.filter(user=request.user).order_by("-created_at")
    unread_count = alert_rows.filter(is_read=False).count()
    read_count = alert_rows.filter(is_read=True).count()
    alert_start = date.today() - timedelta(days=6)
    alert_map = {}
    for item in alert_rows.filter(created_at__date__gte=alert_start):
        created_day = item.created_at.date().isoformat()
        alert_map[created_day] = alert_map.get(created_day, 0) + 1

    alert_labels = []
    alert_values = []
    for offset in range(7):
        current_day = alert_start + timedelta(days=offset)
        day_key = current_day.isoformat()
        alert_labels.append(current_day.strftime("%d %b"))
        alert_values.append(alert_map.get(day_key, 0))
    return render(
        request,
        "public/notifications.html",
        _build_context(request.user, {
            "active_page": "notifications",
            "alerts": alert_rows,
            "notification_labels_json": json.dumps(alert_labels),
            "notification_values_json": json.dumps(alert_values),
            "notification_status_labels_json": json.dumps(["Unread", "Read"]),
            "notification_status_values_json": json.dumps([unread_count, read_count]),
        }),
    )


@ensure_csrf_cookie
def signup_page(request):
    if request.user.is_authenticated:
        return redirect("dashboard_page")

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        phone_number = request.POST.get("phone_number", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not full_name or not email or not password or not confirm_password:
            messages.error(request, "Please fill in all required fields.")
        elif password != confirm_password:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
        else:
            username = _build_unique_username(full_name or email.split("@")[0])
            User.objects.create_user(
                username=username,
                first_name=full_name,
                email=email,
                password=password,
                phone_no=phone_number or None,
            )
            messages.success(request, "Signup successful. Please log in.")
            return redirect("login_page")

    return render(request, "public/signup.html")


@ensure_csrf_cookie
def login_page(request):
    if request.user.is_authenticated:
        return redirect("dashboard_page")

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        if not email or not password:
            messages.error(request, "Please enter both email and password.")
        else:
            # The project uses a custom User model where email is USERNAME_FIELD.
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect("dashboard_page")
            messages.error(request, "Invalid email or password.")

    return render(request, "public/login.html")


def logout_page(request):
    logout(request)
    return redirect("login_page")
