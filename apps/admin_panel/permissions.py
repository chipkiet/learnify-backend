from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """
    Cho phép truy cập chỉ với user có is_staff=True hoặc is_superuser=True.
    """

    message = "Bạn không có quyền truy cập admin panel."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )
