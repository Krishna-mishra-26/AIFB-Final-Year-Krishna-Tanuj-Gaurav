from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'username', 'phone_no', 'is_premium']
    search_fields = ['email', 'username']
    list_filter = ['is_premium']
