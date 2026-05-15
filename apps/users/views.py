import urllib.parse
from django.conf import settings
from django.http import HttpResponseRedirect
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate

from apps.users.serializers.auth_serializers import (
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    ProfileSerializer,
    OTPVerifySerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)

from apps.users.services.google_auth import (
    get_google_tokens,
    get_google_user_info,
    get_or_create_user,
)
from apps.users.services.otp_service import generate_otp, send_otp_email
from apps.users.services.password_reset_service import (
    PasswordResetError,
    initiate_reset,
    confirm_reset,
)

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"message": "Register successful", "email": user.email},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            user = authenticate(request, username=email, password=password)
            if user is None:
                return Response(
                    {"error": "Invalid email or password"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serialized = ChangePasswordSerializer(data=request.data)
        if serialized.is_valid():
            user = request.user
            old_password = serialized.validated_data['old_password']
            new_password = serialized.validated_data['new_password']

            if not user.check_password(old_password):
                return Response(
                    {"error": "Old password is incorrect"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(new_password)
            user.save()
            return Response({"message": "Password changed successfully"})
        return Response(serialized.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        serializer = ProfileSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Email OTP Verification ─────────────────────────────────────────────────────

class SendEmailOTPView(APIView):
    """Generate and send a 6-digit OTP to the authenticated user's email."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.email_verified:
            return Response(
                {"message": "Email của bạn đã được xác thực rồi."},
                status=status.HTTP_200_OK,
            )

        try:
            otp_code = generate_otp(user, purpose="verify_email")
            send_otp_email(user, otp_code, purpose="verify_email")
            return Response(
                {"message": f"Mã OTP đã được gửi đến {user.email}. Vui lòng kiểm tra hộp thư."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": "Không thể gửi email. Vui lòng thử lại sau."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VerifyEmailOTPView(APIView):
    """Verify the OTP submitted by the authenticated user to confirm their email."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        otp_code = serializer.validated_data["otp_code"]

        if not user.is_otp_valid(otp_code, purpose="verify_email"):
            return Response(
                {"error": "Mã OTP không đúng hoặc đã hết hạn. Vui lòng thử lại."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.email_verified = True
        user.save(update_fields=["email_verified"])
        user.clear_otp()

        return Response(
            {"message": "Email đã được xác thực thành công!"},
            status=status.HTTP_200_OK,
        )


# ── Forgot / Reset Password ────────────────────────────────────────────────────

class ForgotPasswordView(APIView):
    """
    Step 1: User provides their email → OTP sent if email is verified.
    Always returns 200 to prevent email enumeration.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]

        try:
            initiate_reset(email)
        except PasswordResetError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(
                {"error": "Không thể gửi email. Vui lòng thử lại sau."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": "Nếu email tồn tại và đã được xác thực, mã OTP đã được gửi đến hộp thư của bạn."},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    """
    Step 2: User provides email + OTP + new password → password is updated.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            confirm_reset(
                email=serializer.validated_data["email"],
                otp_code=serializer.validated_data["otp_code"],
                new_password=serializer.validated_data["new_password"],
            )
        except PasswordResetError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(
                {"error": "Có lỗi xảy ra. Vui lòng thử lại sau."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": "Mật khẩu đã được đặt lại thành công. Bạn có thể đăng nhập với mật khẩu mới."},
            status=status.HTTP_200_OK,
        )


# ── Google OAuth ───────────────────────────────────────────────────────────────

class GoogleLoginView(APIView):
    """Redirect user sang trang đăng nhập Google."""

    permission_classes = [AllowAny]

    def get(self, request):
        params = urllib.parse.urlencode(
            {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "response_type": "code",
                "scope": "openid email profile",
                "access_type": "offline",
            }
        )
        google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{params}"
        return HttpResponseRedirect(google_auth_url)


class GoogleCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.query_params.get("code")

        if not code:
            return Response(
                {"error": "Missing authorization code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            google_tokens = get_google_tokens(code)
            access_token = google_tokens["access_token"]

            user_info = get_google_user_info(access_token)
            user, _ = get_or_create_user(user_info)

            # Issue JWT bằng SimpleJWT
            refresh = RefreshToken.for_user(user)
            jwt_access = str(refresh.access_token)
            jwt_refresh = str(refresh)

            # Redirect về frontend kèm token trong URL fragment
            frontend_url = settings.GOOGLE_LOGIN_REDIRECT_URL
            redirect_url = f"{frontend_url}#access={jwt_access}&refresh={jwt_refresh}"
            return HttpResponseRedirect(redirect_url)

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

