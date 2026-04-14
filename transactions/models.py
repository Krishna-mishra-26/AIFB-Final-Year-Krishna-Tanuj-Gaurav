from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
import uuid
from datetime import datetime

User = get_user_model()


class Category(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"

class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    category_type = models.CharField(max_length=50, choices=[('income', 'Income'), ('expense', 'Expense')], default='expense')
    description = models.TextField(blank=True, null=True)
    date = models.DateField()
    currency = models.CharField(max_length=3, choices=[('USD', 'USD'), ('EUR', 'EUR'), ('INR', 'INR')], default='INR')
    created_at = models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} ({self.category})"




class alerts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='transaction_alerts')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.message}"



class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=255)
    monthly_limit = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class BudgetHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=255)
    month = models.IntegerField()  # Stores the month (1-12)
    year = models.IntegerField()  # Stores the year (2023, 2024, etc.)
    previous_limit = models.DecimalField(max_digits=10, decimal_places=2)
    actual_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    suggested_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ('user', 'category', 'month', 'year')  # Prevents duplicate records
