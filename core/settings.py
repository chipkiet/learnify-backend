from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ══════════════════════════════════════════════════════
# ENVIRONMENT DETECTION
# ══════════════════════════════════════════════════════
IS_PRODUCTION = bool(
    os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PRODUCTION")
)

# ══════════════════════════════════════════════════════
# SECURITY
# ══════════════════════════════════════════════════════
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-key-replace-in-production")

DEBUG = not IS_PRODUCTION

if IS_PRODUCTION:
    ALLOWED_HOSTS = [
        os.environ.get("RAILWAY_PUBLIC_DOMAIN", ""),
        ".railway.app",
        "api.learnify.info.vn",
    ]
else:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# ══════════════════════════════════════════════════════
# APPLICATIONS
# ══════════════════════════════════════════════════════
DJANGO_APPS = [
    "unfold",  # <-- BẮT BUỘC PHẢI ĐỨNG TRƯỚC django.contrib.admin
    "unfold.contrib.filters",  # Cung cấp filter UI đẹp hơn
    "unfold.contrib.forms",  # Cung cấp form UI đẹp hơn
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework_simplejwt.token_blacklist",
]

THIRD_PARTY_APPS = [
    "rest_framework",
]

LOCAL_APPS = [
    "apps.users",
    "apps.tags",
    "apps.documents",
    "apps.flashcards",
    "apps.ai",
    "apps.study",
    "apps.quiz",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ══════════════════════════════════════════════════════
# MIDDLEWARE
# ══════════════════════════════════════════════════════
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # phải sau SecurityMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ══════════════════════════════════════════════════════
# URLS / WSGI
# ══════════════════════════════════════════════════════
ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"

# ══════════════════════════════════════════════════════
# TEMPLATES
# ══════════════════════════════════════════════════════
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ══════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════
if IS_PRODUCTION:
    DATABASES = {
        "default": dj_database_url.config(
            default=os.environ.get("DATABASE_URL"),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "learnify_db",
            "USER": "learnify_user",
            "PASSWORD": "quetvaque700716",
            "HOST": "db",
            "PORT": "5432",
        }
    }

# ══════════════════════════════════════════════════════
# STATIC FILES
# ══════════════════════════════════════════════════════
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

if IS_PRODUCTION:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

# ══════════════════════════════════════════════════════
# MEDIA FILES (uploaded documents)
# ══════════════════════════════════════════════════════
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ══════════════════════════════════════════════════════
# CORS
# ══════════════════════════════════════════════════════
if IS_PRODUCTION:
    CORS_ALLOWED_ORIGINS = [
        os.environ.get("FRONTEND_URL", "").rstrip("/"),
    ]
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r"^https://.*\.vercel\.app$",
    ]
else:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

CORS_ALLOW_CREDENTIALS = True

# ══════════════════════════════════════════════════════
# AUTHENTICATION
# ══════════════════════════════════════════════════════
AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 7,
        }
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "apps.users.validators.LetterAndNumberValidator"},
]

# ══════════════════════════════════════════════════════
# DJANGO REST FRAMEWORK
# ══════════════════════════════════════════════════════
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

# ══════════════════════════════════════════════════════
# SIMPLE JWT
# ══════════════════════════════════════════════════════
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKEN": True,
    "BLACKLIST_AFTER_ROTATE": True,
}

# ══════════════════════════════════════════════════════
# THIRD PARTY API KEYS
# ══════════════════════════════════════════════════════
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# ══════════════════════════════════════════════════════
# INTERNATIONALISATION
# ══════════════════════════════════════════════════════
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True

# ══════════════════════════════════════════════════════
# MISC
# ══════════════════════════════════════════════════════
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Production security headers (chỉ bật khi HTTPS)
if IS_PRODUCTION:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


# ══════════════════════════════════════════════════════
# UNFOLD ADMIN SETTINGS
# ══════════════════════════════════════════════════════
from django.templatetags.static import static

UNFOLD = {
    "SITE_TITLE": "Learnify AI Admin",
    "SITE_HEADER": "Learnify Management",
    "SITE_URL": "/",
    "SITE_ICON": {
        "light": lambda request: static(
            "icon-light.svg"
        ),  # Bạn có thể thay bằng icon của bạn sau
        "dark": lambda request: static("icon-dark.svg"),
    },
    "COLORS": {
        "primary": {
            "50": "250 253 255",
            "100": "240 249 255",
            "200": "224 242 254",
            "300": "186 230 253",
            "400": "125 211 252",
            "500": "56 189 248",
            "600": "2 132 199",  # Màu chủ đạo (Xanh dương hiện đại)
            "700": "3 105 161",
            "800": "7 89 133",
            "900": "12 74 110",
        },
    },
}

# ══════════════════════════════════════════════════════
# Google Domain
# ══════════════════════════════════════════════════════
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

if IS_PRODUCTION:
    GOOGLE_REDIRECT_URI = os.environ.get(
        "GOOGLE_REDIRECT_URI", "https://api.learnify.info.vn/api/auth/google/callback/"
    )
    GOOGLE_LOGIN_REDIRECT_URL = os.environ.get(
        "GOOGLE_LOGIN_REDIRECT_URL", "https://learnify.info.vn/auth/callback"
    )
else:
    GOOGLE_REDIRECT_URI = os.environ.get(
        "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback/"
    )
    GOOGLE_LOGIN_REDIRECT_URL = os.environ.get(
        "GOOGLE_LOGIN_REDIRECT_URL", "http://localhost:5173/auth/callback"
    )
