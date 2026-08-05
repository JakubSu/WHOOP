import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


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


DEBUG = env_bool("DEBUG", True)


def load_ssm_parameters() -> None:
    if DEBUG:
        return

    prefix = os.environ.get("SSM_PARAMETER_PREFIX", "").rstrip("/")
    if not prefix:
        raise RuntimeError("SSM_PARAMETER_PREFIX must be configured when DEBUG=false.")

    parameter_names = {
        "SECRET_KEY": "django/secret-key",
        "OPENAI_API_KEY": "openai/api-key",
        "WHOOP_CLIENT_ID": "whoop/client-id",
        "WHOOP_CLIENT_SECRET": "whoop/client-secret",
        "WHOOP_TOKEN_ENCRYPTION_KEY": "whoop/token-encryption-key",
        "POSTGRES_PASSWORD": "postgres/password",
    }
    missing_env_keys = [key for key in parameter_names if not os.environ.get(key)]
    if not missing_env_keys:
        return

    import boto3

    names_by_key = {key: f"{prefix}/{parameter_names[key]}" for key in missing_env_keys}
    client = boto3.client("ssm", region_name=os.environ.get("AWS_REGION"))
    response = client.get_parameters(
        Names=list(names_by_key.values()),
        WithDecryption=True,
    )
    values_by_name = {
        parameter["Name"]: parameter["Value"]
        for parameter in response.get("Parameters", [])
    }

    missing_parameters = [
        name for name in names_by_key.values() if name not in values_by_name
    ]
    if missing_parameters:
        raise RuntimeError(
            "Missing required SSM parameters: " + ", ".join(sorted(missing_parameters))
        )

    for key, name in names_by_key.items():
        os.environ[key] = values_by_name[name]


load_ssm_parameters()

SECRET_KEY = os.environ.get(
    "SECRET_KEY", "dev-only-secret-key-for-whoop-api-local-jwt-signing-2026"
)
ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1"),
)
CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS", "http://localhost,http://127.0.0.1"
)

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
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

if not DEBUG or os.environ.get("DATABASE_ENGINE") == "postgres":
    DATABASES = {
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
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
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

JWT_REFRESH_COOKIE_NAME = os.environ.get("JWT_REFRESH_COOKIE_NAME", "whoop_refresh")
JWT_REFRESH_COOKIE_SECURE = env_bool("JWT_REFRESH_COOKIE_SECURE", not DEBUG)
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
    "read:recovery read:cycles read:workout read:sleep read:profile read:body_measurement offline",
)
WHOOP_TOKEN_ENCRYPTION_KEY = os.environ.get("WHOOP_TOKEN_ENCRYPTION_KEY", "")
WHOOP_FRONTEND_SUCCESS_URL = os.environ.get("WHOOP_FRONTEND_SUCCESS_URL", "")
WHOOP_FRONTEND_ALLOWED_ORIGINS = env_list(
    "WHOOP_FRONTEND_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)
WHOOP_OAUTH_STATE_TTL_SECONDS = int(
    os.environ.get("WHOOP_OAUTH_STATE_TTL_SECONDS", "600")
)

AI_LLM_PROVIDER = os.environ.get("AI_LLM_PROVIDER", "openai")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_TIMEOUT = float(os.environ.get("OPENAI_TIMEOUT", "30"))

# The echo runner makes local message and SSE contract testing possible without a model.
# Production remains unavailable until the real coach agent adapter is configured.
COACH_RUNNER_FACTORY = os.environ.get(
    "COACH_RUNNER_FACTORY",
    "coach.implementations.echo.create_echo_runner"
    if DEBUG
    else "coach.runner.create_unavailable_runner",
)
COACH_ECHO_THINK_SECONDS = float(os.environ.get("COACH_ECHO_THINK_SECONDS", "0.5"))

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_LLM_PAYLOADS = env_bool("LOG_LLM_PAYLOADS", False)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django.server": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "ai": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "coach": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "recommendation": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "training": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "whoop": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
