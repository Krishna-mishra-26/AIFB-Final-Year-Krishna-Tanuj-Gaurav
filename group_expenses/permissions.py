from rest_framework.permissions import BasePermission

class IsGroupMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.members.filter(user=request.user).exists()
