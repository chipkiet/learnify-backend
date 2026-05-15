from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


class AuthProvider(models.TextChoices):
    LOCAL = "local", "Local"
    GOOGLE = "google", "Google"


class OtpPurpose(models.TextChoices):
    VERIFY_EMAIL = "verify_email", "Verify Email"
    RESET_PASSWORD = "reset_password", "Reset Password"


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required, input this now !!!")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150, blank=True)
    avatar = models.URLField(max_length=500, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    auth_provider = models.CharField(
        max_length=10,
        choices=AuthProvider.choices,
        default=AuthProvider.LOCAL,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ── Verification status ────────────────────────────
    # Google users get email_verified=True automatically (Google already verified it)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)

    # ── OTP fields ─────────────────────────────────────
    otp_code = models.CharField(max_length=6, blank=True, default="")
    otp_expires_at = models.DateTimeField(null=True, blank=True)
    otp_purpose = models.CharField(
        max_length=30,
        choices=OtpPurpose.choices,
        blank=True,
        default="",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    def __str__(self):
        return self.email

    def is_otp_valid(self, code: str, purpose: str) -> bool:
        """Check if provided OTP is correct, unexpired, and matches purpose."""
        if not self.otp_code or not self.otp_expires_at:
            return False
        if self.otp_purpose != purpose:
            return False
        if self.otp_expires_at < timezone.now():
            return False
        return self.otp_code == code

    def clear_otp(self):
        """Wipe OTP fields after successful use."""
        self.otp_code = ""
        self.otp_expires_at = None
        self.otp_purpose = ""
        self.save(update_fields=["otp_code", "otp_expires_at", "otp_purpose"])
