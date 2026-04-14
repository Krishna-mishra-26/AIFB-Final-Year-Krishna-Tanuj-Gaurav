# transactions/admin.py
from django.contrib import admin
from .models import Transaction, Category, Budget

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'category', 'date', 'category_type')
    search_fields = ('user__username', 'category')
    list_filter = ('category_type', 'date')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
    search_fields = ('name', 'user__username')

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'monthly_limit', 'created_at')
    search_fields = ('user__username', 'category__name')
