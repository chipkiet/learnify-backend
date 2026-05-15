import requests
from django.conf import settings
from apps.users.models import User, AuthProvider


GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def get_google_tokens(code: str) -> dict:
    response = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
    )
    response.raise_for_status()
    return response.json()


def get_google_user_info(access_token: str) -> dict:
    response = requests.get(
        GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
    )
    response.raise_for_status()
    return response.json()


def get_or_create_user(user_info: dict) -> tuple[User, bool]:
    email = user_info.get("email", "")
    full_name = user_info.get("name", "")
    avatar = user_info.get("picture", "")

    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "full_name": full_name,
            "avatar": avatar,
            "auth_provider": AuthProvider.GOOGLE,
            "is_active": True,
            "email_verified": True,  # Google đã xác thực email rồi
        },
    )

    if created:
        user.set_unusable_password()  # khoá login bằng password
        user.save(update_fields=["password"])
    else:
        # Đăng nhập lại → cập nhật avatar + đảm bảo email_verified = True
        updated_fields = []
        if avatar and user.avatar != avatar:
            user.avatar = avatar
            updated_fields.append("avatar")
        if not user.email_verified:
            user.email_verified = True
            updated_fields.append("email_verified")
        if updated_fields:
            user.save(update_fields=updated_fields)

    return user, created
