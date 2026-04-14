from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create the router and register the viewsets
router = DefaultRouter()
router.register(r'groups', views.GroupViewSet)
router.register(r'group-expenses', views.GroupExpenseViewSet)
router.register(r'group-members', views.GroupMemberViewSet)
router.register(r'settlements', views.SettlementViewSet)

# Define the URL patterns
urlpatterns = [
    # Include the router-generated URLs for the API endpoints
    path('api/', include(router.urls)),

    # Frontend views
    path('group-expenses/', views.group_expenses_view, name='group_expenses'),
    path('add-expense/', views.add_expense, name='add_expense'),
]
