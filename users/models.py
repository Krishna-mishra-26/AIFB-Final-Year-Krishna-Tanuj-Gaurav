from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
import uuid



class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone_no = models.CharField(max_length=15, blank=True, null=True)
    is_premium = models.BooleanField(default=False)
    
    # Role-Based Fields
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    def __str__(self):
        return self.username





class FinancialData(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    monthly_income_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    monthly_income_business = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    monthly_income_freelance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    monthly_income_other = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    rent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bills = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    loans = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    subscriptions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    savings_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    savings_stocks = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    savings_crypto = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    savings_real_estate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    total_debt = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username} - Financial Data"


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatar/', blank=True, null=True)
    preferred_currency = models.CharField(max_length=3, choices=[
        ('USD', 'USD'),
        ('INR', 'INR'),
        ('EUR', 'EUR')
    ], default='INR')
    date_of_birth = models.DateField(null=True, blank=True)
    occupation = models.CharField(max_length=20, choices=[
        ('Student', 'Student'),
        ('Employee', 'Employee'),
        ('Business', 'Business'),
        ('Retired', 'Retired')
    ])
    annual_income = models.CharField(max_length=20, choices=[
        ('<10K', '<$10K'),
        ('10K-50K', '$10K-$50K'),
        ('50K-100K', '$50K-$100K'),
        ('100K+', '$100K+')
    ])
    financial_goal = models.CharField(max_length=50, choices=[
        ('Savings', 'Savings'),
        ('Investment', 'Investment'),
        ('Budgeting', 'Budgeting'),
        ('Debt Management', 'Debt Management')
    ])
    investment_risk = models.CharField(max_length=10, choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High')
    ])
    subscription_plan = models.CharField(max_length=10, choices=[
        ('Free', 'Free'),
        ('Premium', 'Premium')
    ])

    def __str__(self):
        return f"{self.user.username} - {self.financial_goal}"
    

