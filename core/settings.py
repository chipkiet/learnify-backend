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
    ]
else:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# ══════════════════════════════════════════════════════
# APPLICATIONS
# ══════════════════════════════════════════════════════
DJANGO_APPS = [
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
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

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
        os.environ.get("FRONTEND_URL", ""),
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
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
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
