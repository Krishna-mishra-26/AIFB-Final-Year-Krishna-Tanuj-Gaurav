"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from backend import views as public_views



urlpatterns = [
    path('', public_views.home, name='home'),
    path('dashboard/', public_views.dashboard_page, name='dashboard_page'),
    path('transaction/', public_views.transactions_page, name='transaction_page'),
    path('transactions/', public_views.transactions_page, name='transactions_page'),
    path('budget/', public_views.budget_page, name='budget_page'),
    path('goals/', public_views.goals_page, name='goals_page'),
    path('group-expenses/', public_views.group_expenses_page, name='group_expenses_page'),
    path('recurring/', public_views.recurring_page, name='recurring_page'),
    path('notifications/', public_views.notifications_page, name='notifications_page'),
    path('signup/', public_views.signup_page, name='signup_page'),
    path('login/', public_views.login_page, name='login_page'),
    path('logout/', public_views.logout_page, name='logout_page'),
    path('admin/', admin.site.urls),

    # JWT Authentication Routes
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Login
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh token

    # Group Expenses API Routes
    path('api/group-expenses/', include('group_expenses.urls')),  # Include the group_expenses URLs
    path('api/users/', include('users.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/insights/', include('insights.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/frontend/', include('frontend.urls')),
    path('admin-dashboard/', include('admin_dashboard.urls')),
  
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

