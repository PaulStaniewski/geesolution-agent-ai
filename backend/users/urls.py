from django.urls import path
from .views import (
    register,
    user_info,
    logout,
    EmailTokenObtainView,
    CustomTokenRefreshView,
    password_reset_request,
    password_reset_confirm,
)

urlpatterns = [
    path("register/", register, name="auth-register"),
    path("me/", user_info, name="auth-me"),
    path("logout/", logout, name="auth-logout"),
    path("token/", EmailTokenObtainView.as_view(), name="auth-token-obtain"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="auth-token-refresh"),
    path("password-reset/", password_reset_request, name="auth-password-reset"),
    path("password-reset-confirm/", password_reset_confirm, name="auth-password-reset-confirm"),
]