# transactions/utils.py
from .models import alerts, Budget, Transaction
from django.db.models import Sum
import joblib
import os

def check_budget_alert(user):
    budgets = Budget.objects.filter(user=user)
    for budget in budgets:
        spent = Transaction.objects.filter(
            user=user,
            category__name__iexact=budget.category,
            category_type='expense'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        usage_percentage = (spent / budget.monthly_limit) * 100 if budget.monthly_limit > 0 else 0
        
        if usage_percentage >= 80:
            alerts.objects.create(
                user=user,
                message=f"You have used {usage_percentage:.2f}% of your budget for {budget.category}. Consider reviewing your spending."
            )



# Load the model and vectorizer at startup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(BASE_DIR, "transaction_classifier.pkl")
VECTORIZER_PATH = os.path.join(BASE_DIR, "transaction_vectorizer.pkl")

classifier = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)


def categorize_transaction(description):
    """Predicts category for a given transaction description"""
    X_new = vectorizer.transform([description])
    predicted_category = classifier.predict(X_new)[0]
    return predicted_category
