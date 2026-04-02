from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.admin_panel.serializers import (
    AdminLoginSerializer,
    AdminUserSerializer,
    AdminStatsSerializer,
)
from apps.admin_panel.permissions import IsAdminUser


class AdminLoginView(APIView):
    """
    POST /api/admin-panel/login/
    Chỉ cho phép user có is_staff=True hoặc is_superuser=True.
    Trả về JWT access + refresh token.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = authenticate(request, username=email, password=password)

        if user is None:
            return Response(
                {"detail": "Email hoặc mật khẩu không chính xác."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not (user.is_staff or user.is_superuser):
            return Response(
                {"detail": "Tài khoản này không có quyền truy cập admin panel."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user.is_active:
            return Response(
                {"detail": "Tài khoản này đã bị vô hiệu hóa."},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": AdminUserSerializer(
                    {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name,
                        "is_staff": user.is_staff,
                        "is_superuser": user.is_superuser,
                    }
                ).data,
            },
            status=status.HTTP_200_OK,
        )


class AdminStatsView(APIView):
    """
    GET /api/admin-panel/stats/
    Trả về số liệu tổng quan cho dashboard.
    Yêu cầu: is_staff=True hoặc is_superuser=True.
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        from django.contrib.auth import get_user_model
        from apps.documents.models import Document
        from apps.flashcards.models import FlashcardSet, FlashCard

        User = get_user_model()
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())

        stats = {
            "total_users": User.objects.count(),
            "active_users": User.objects.filter(is_active=True).count(),
            "total_documents": Document.objects.count(),
            "total_flashcard_sets": FlashcardSet.objects.count(),
            "total_flashcards": FlashCard.objects.count(),
            "new_users_today": User.objects.filter(
                created_at__gte=today_start
            ).count(),
            "new_users_this_week": User.objects.filter(
                created_at__gte=week_start
            ).count(),
        }

        serializer = AdminStatsSerializer(stats)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminUsersListView(APIView):
    """
    GET /api/admin-panel/users/
    Trả về danh sách users với thông tin cơ bản.
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        users = User.objects.order_by("-created_at").values(
            "id",
            "email",
            "full_name",
            "is_active",
            "is_staff",
            "auth_provider",
            "created_at",
        )

        return Response(
            {
                "count": users.count(),
                "results": list(users),
            },
            status=status.HTTP_200_OK,
        )
