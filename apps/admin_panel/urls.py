from django.urls import path
from apps.admin_panel.views import AdminLoginView, AdminStatsView, AdminUsersListView

urlpatterns = [
    path("login/", AdminLoginView.as_view(), name="admin-login"),
    path("stats/", AdminStatsView.as_view(), name="admin-stats"),
    path("users/", AdminUsersListView.as_view(), name="admin-users"),
]
