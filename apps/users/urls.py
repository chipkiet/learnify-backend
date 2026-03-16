from django.urls import path
from apps.users.views import RegisterView, LoginView, ChangePasswordView, ProfileView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('me/', ProfileView.as_view(), name='profile')
]