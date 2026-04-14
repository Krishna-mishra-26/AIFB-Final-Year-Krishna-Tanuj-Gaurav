import pandas as pd
from datetime import datetime, timedelta
from transactions.models import Transaction, Budget
from sklearn.linear_model import LinearRegression
from insights.models import SavingsGoal
import numpy as np

def get_spending_insights(user):
    """Generates spending insights per category."""
    transactions = Transaction.objects.filter(user=user).values("category", "amount", "date")
    
    if not transactions:
        return []

    df = pd.DataFrame(transactions)
    df["date"] = pd.to_datetime(df["date"])
    
    insights = df.groupby("category").agg(
        total_spent=pd.NamedAgg(column="amount", aggfunc="sum"),
        avg_spent=pd.NamedAgg(column="amount", aggfunc="mean")
    ).reset_index()

    return insights.to_dict("records")

def predict_future_spending(user, category):
    """Predicts future spending based on past transactions using Linear Regression."""
    transactions = Transaction.objects.filter(user=user, category=category).values("amount", "date")

    if len(transactions) < 3:
        return "Insufficient data for forecasting"

    df = pd.DataFrame(transactions)
    df["date"] = pd.to_datetime(df["date"])
    df["days"] = (df["date"] - df["date"].min()).dt.days
    
    X = df[["days"]].values
    y = df["amount"].values

    model = LinearRegression()
    model.fit(X, y)

    future_date = (datetime.today() - df["date"].min()).days + 30
    future_spending = model.predict(np.array([[future_date]]))[0]

    return round(future_spending, 2)

def suggest_savings(user):
    """Suggests cost-cutting tips based on spending behavior."""
    insights = get_spending_insights(user)

    suggestions = []
    for item in insights:
        if item["total_spent"] > 1000:  # Example threshold
            suggestions.append(f"Reduce spending in {item['category']} to save more.")

    return suggestions



def track_savings_progress(user):
    """Automatically updates the saved amount in savings goals based on transactions."""
    goals = SavingsGoal.objects.filter(user=user, status="In Progress")

    for goal in goals:
        savings = Transaction.objects.filter(user=user, category="Savings", date__lte=goal.deadline).aggregate(total_savings=models.Sum("amount"))["total_savings"] or 0.0
        goal.saved_amount = savings
        goal.update_progress()  # Update goal status if reached
        goal.save()
    
    return goals
