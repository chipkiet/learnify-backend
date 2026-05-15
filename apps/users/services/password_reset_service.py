from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.users.services.otp_service import generate_otp, send_otp_email

User = get_user_model()


class PasswordResetError(Exception):
    """Raised for expected failures during the reset flow."""
    pass


def initiate_reset(email: str) -> None:
    """
    Step 1 of forgot-password flow.
    - Finds user by email
    - Ensures email is verified (otherwise reset cannot be trusted)
    - Generates OTP and sends email

    Always returns None — never raises for "user not found" to prevent
    email enumeration attacks. Raises PasswordResetError only for
    recoverable UX errors (email not verified).
    """
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Silent — do not reveal whether email exists
        return

    if not user.email_verified:
        raise PasswordResetError(
            "Email của bạn chưa được xác thực. "
            "Vui lòng đăng nhập và xác thực email trong phần Cài đặt trước khi đặt lại mật khẩu."
        )

    otp_code = generate_otp(user, purpose="reset_password")
    send_otp_email(user, otp_code, purpose="reset_password")


def confirm_reset(email: str, otp_code: str, new_password: str) -> None:
    """
    Step 2 of forgot-password flow.
    - Validates OTP
    - Sets new password
    - Clears OTP fields
    Raises PasswordResetError on any failure.
    """
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        raise PasswordResetError("Không tìm thấy tài khoản với email này.")

    if not user.is_otp_valid(otp_code, purpose="reset_password"):
        raise PasswordResetError("Mã OTP không hợp lệ hoặc đã hết hạn.")

    try:
        validate_password(new_password, user=user)
    except ValidationError as e:
        raise PasswordResetError(" ".join(e.messages))

    user.set_password(new_password)
    user.save(update_fields=["password"])
    user.clear_otp()
