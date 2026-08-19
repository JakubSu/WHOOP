"""Shared Django settings and helpers."""

import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env_list(name: str, default: str) -> list[str]:
    return [
        value.strip()
        for value in os.environ.get(name, default).split(",")
        if value.strip()
    ]


def env_bool(name: str, default: bool) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def required_env(name: str) -> str:
    """Return a required deployment input with a clear startup failure."""

    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} must be configured.")
    return value


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "rest_framework_simplejwt.token_blacklist",
    "users.apps.UsersConfig",
    "training.apps.TrainingConfig",
    "recommendation.apps.RecommendationConfig",
    "coach.apps.CoachConfig",
    "whoop.apps.WhoopConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.User"

# Local-development defaults. production.py replaces stable production values and
# requires its secrets explicitly.
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "dev-only-secret-key-for-whoop-api-local-jwt-signing-2026"
)
ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS", os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1")
)
CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS", "http://localhost,http://127.0.0.1"
)
JWT_REFRESH_COOKIE_NAME = os.environ.get("JWT_REFRESH_COOKIE_NAME", "whoop_refresh")
JWT_REFRESH_COOKIE_SECURE = env_bool("JWT_REFRESH_COOKIE_SECURE", False)
JWT_REFRESH_COOKIE_SAMESITE = os.environ.get("JWT_REFRESH_COOKIE_SAMESITE", "Lax")
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://127.0.0.1:5500,http://localhost:5500,http://127.0.0.1:5173,http://localhost:5173",
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "origin",
    "user-agent",
    "x-requested-with",
]

WHOOP_CLIENT_ID = os.environ.get("WHOOP_CLIENT_ID", "")
WHOOP_CLIENT_SECRET = os.environ.get("WHOOP_CLIENT_SECRET", "")
WHOOP_REDIRECT_URI = os.environ.get(
    "WHOOP_REDIRECT_URI", "http://localhost:8000/api/v1/whoop/callback/"
)
WHOOP_SCOPES = os.environ.get(
    "WHOOP_SCOPES",
    "read:recovery read:cycles read:workout read:sleep read:profile "
    "read:body_measurement offline",
)
WHOOP_TOKEN_ENCRYPTION_KEY = os.environ.get("WHOOP_TOKEN_ENCRYPTION_KEY", "")
WHOOP_FRONTEND_SUCCESS_URL = os.environ.get("WHOOP_FRONTEND_SUCCESS_URL", "")
WHOOP_FRONTEND_ALLOWED_ORIGINS = env_list(
    "WHOOP_FRONTEND_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)
WHOOP_ALLOWED_USER_EMAILS = {
    email.lower()
    for email in env_list("WHOOP_ALLOWED_USER_EMAILS", "")
    if email
}
WHOOP_OAUTH_STATE_TTL_SECONDS = int(
    os.environ.get("WHOOP_OAUTH_STATE_TTL_SECONDS", "600")
)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.6-luna")
COACH_RUN_TIMEOUT_SECONDS = float(
    os.environ.get("COACH_RUN_TIMEOUT_SECONDS", "45")
)
COACH_CONTEXT_RECENT_TURNS = int(os.environ.get("COACH_CONTEXT_RECENT_TURNS", "3"))
COACH_CONTEXT_TOKEN_RESERVE = int(
    os.environ.get("COACH_CONTEXT_TOKEN_RESERVE", "4000")
)
COACH_MAX_MODEL_REQUESTS = int(os.environ.get("COACH_MAX_MODEL_REQUESTS", "6"))
COACH_MAX_TOOL_CALLS = int(os.environ.get("COACH_MAX_TOOL_CALLS", "12"))
COACH_MAX_INPUT_TOKENS = int(os.environ.get("COACH_MAX_INPUT_TOKENS", "40000"))
COACH_MAX_OUTPUT_TOKENS = int(os.environ.get("COACH_MAX_OUTPUT_TOKENS", "4000"))
COACH_MAX_INPUT_TOKENS_PER_REQUEST = int(
    os.environ.get("COACH_MAX_INPUT_TOKENS_PER_REQUEST", "12000")
)
COACH_TOOL_TIMEOUT_SECONDS = float(os.environ.get("COACH_TOOL_TIMEOUT_SECONDS", "10"))
COACH_STREAM_KEEPALIVE_SECONDS = float(
    os.environ.get("COACH_STREAM_KEEPALIVE_SECONDS", "15")
)
COACH_MAX_COST_USD = os.environ.get("COACH_MAX_COST_USD", "0.05")
COACH_USER_MONTHLY_BUDGET_USD = os.environ.get(
    "COACH_USER_MONTHLY_BUDGET_USD", "2.00"
)
COACH_GLOBAL_MONTHLY_BUDGET_USD = os.environ.get(
    "COACH_GLOBAL_MONTHLY_BUDGET_USD", "20.00"
)
COACH_DEMO_TOTAL_BUDGET_USD = os.environ.get("COACH_DEMO_TOTAL_BUDGET_USD", "0.03")
COACH_DEMO_MAX_COST_USD = os.environ.get("COACH_DEMO_MAX_COST_USD", "0.005")
DEMO_SESSION_TTL_SECONDS = int(os.environ.get("DEMO_SESSION_TTL_SECONDS", "3600"))
COACH_LOGFIRE_ENABLED = env_bool("COACH_LOGFIRE_ENABLED", False)
COACH_LOGFIRE_CAPTURE_CONTENT = env_bool("COACH_LOGFIRE_CAPTURE_CONTENT", False)
COACH_LOGFIRE_CAPTURE_BINARY_CONTENT = env_bool(
    "COACH_LOGFIRE_CAPTURE_BINARY_CONTENT", False
)
COACH_LOGFIRE_CAPTURE_MODEL_REQUEST_PARAMETERS = env_bool(
    "COACH_LOGFIRE_CAPTURE_MODEL_REQUEST_PARAMETERS", False
)
LOGFIRE_TOKEN = os.environ.get("LOGFIRE_TOKEN", "")
LOGFIRE_SERVICE_NAME = os.environ.get("LOGFIRE_SERVICE_NAME", "whoop-coach")
COACH_RUNNER_FACTORY = os.environ.get(
    "COACH_RUNNER_FACTORY", "ai.implementations.echo.create_echo_runner"
)
COACH_ECHO_THINK_SECONDS = float(os.environ.get("COACH_ECHO_THINK_SECONDS", "0.5"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "users.authentication.DemoAwareJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
SPECTACULAR_SETTINGS = {
    "TITLE": "WHOOP AI Coach API",
    "DESCRIPTION": (
        "API for authentication, WHOOP connection management, training plans, workouts, "
        "exercise libraries, and AI-generated workout recommendations."
    ),
    "VERSION": "1.0.0",
}
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}


def build_logging(log_level: str) -> dict:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "standard"}
        },
        "root": {"handlers": ["console"], "level": log_level},
        "loggers": {
            name: {"handlers": ["console"], "level": log_level, "propagate": False}
            for name in (
                "django.server",
                "ai",
                "coach",
                "recommendation",
                "training",
                "whoop",
                "uvicorn.access",
            )
        },
    }


def postgres_database() -> dict:
    """Build the shared PostgreSQL connection configuration."""

    return {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": os.environ.get("POSTGRES_HOST", "db"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
            "NAME": os.environ.get("POSTGRES_DB", "whoop_ai_coach"),
            "USER": os.environ.get("POSTGRES_USER", "whoop_ai_coach"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
            "CONN_MAX_AGE": int(os.environ.get("POSTGRES_CONN_MAX_AGE", "60")),
        }
    }
