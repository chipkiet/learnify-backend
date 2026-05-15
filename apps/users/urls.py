from django.urls import path

from apps.users.views import (
    RegisterView,
    LoginView,
    ChangePasswordView,
    ProfileView,
    GoogleCallbackView,
    GoogleLoginView,
    SendEmailOTPView,
    VerifyEmailOTPView,
    ForgotPasswordView,
    ResetPasswordView,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", ProfileView.as_view(), name="profile"),

    # Email OTP verification (requires auth)
    path("otp/send-email/", SendEmailOTPView.as_view(), name="otp-send-email"),
    path("otp/verify-email/", VerifyEmailOTPView.as_view(), name="otp-verify-email"),

    # Forgot / Reset password (public)
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),

    # Google OAuth
    path("google/", GoogleLoginView.as_view(), name="google-login"),
    path("google/callback/", GoogleCallbackView.as_view(), name="google-callback"),
]
