# users/permissions.py
from rest_framework.permissions import BasePermission

class IsPremiumUser(BasePermission):
    """Allow access only to premium users."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_premium
