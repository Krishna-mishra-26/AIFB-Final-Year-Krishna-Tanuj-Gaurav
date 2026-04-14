from django.db import models
from django.conf import settings
from datetime import datetime

class BudgetInsight(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.CharField(max_length=100, default="General")
    average_spending = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    forecasted_spending = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    savings_recommendation = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return f"{self.user.username} - {self.category} Insights"




class SavingsGoal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    goal_name = models.CharField(max_length=255)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    saved_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    deadline = models.DateField()
    status = models.CharField(max_length=20, choices=[("In Progress", "In Progress"), ("Completed", "Completed")], default="In Progress")
    created_at = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return f"{self.user.username} - {self.goal_name}"

    def update_progress(self):
        """Updates the status based on savings progress."""
        if self.saved_amount >= self.target_amount:
            self.status = "Completed"
            self.save()
