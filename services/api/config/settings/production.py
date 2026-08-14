"""Production settings with fixed infrastructure and explicit secret inputs."""

import os

from .base import *

ENVIRONMENT = "production"
DEBUG = False

# APP_DOMAIN is a required deployment identity shared with Caddy, not an optional
# application override. The remaining public URLs are derived from it.
APP_DOMAIN = required_env("APP_DOMAIN")
ALLOWED_HOSTS = [APP_DOMAIN]
CSRF_TRUSTED_ORIGINS = [f"https://{APP_DOMAIN}"]
CORS_ALLOWED_ORIGINS = [f"https://{APP_DOMAIN}"]
WHOOP_FRONTEND_ALLOWED_ORIGINS = [f"https://{APP_DOMAIN}"]
WHOOP_FRONTEND_SUCCESS_URL = f"https://{APP_DOMAIN}/connect-whoop/success"
WHOOP_REDIRECT_URI = f"https://{APP_DOMAIN}/api/v1/whoop/callback/"
JWT_REFRESH_COOKIE_SECURE = True

# These values describe the single production topology and are intentionally
# not configurable through the container environment.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": "db",
        "PORT": "5432",
        "NAME": "whoop_ai_coach",
        "USER": "whoop_ai_coach",
        "PASSWORD": required_env("POSTGRES_PASSWORD"),
        "CONN_MAX_AGE": 60,
    }
}
OPENAI_TIMEOUT = 30.0
COACH_RUNNER_FACTORY = "ai.implementations.pydantic_coach.create_pydantic_coach_runner"
LOGFIRE_SERVICE_NAME = "whoop-coach"

# Secrets are injected by the deployment process and are never given defaults.
SECRET_KEY = required_env("SECRET_KEY")
OPENAI_API_KEY = required_env("OPENAI_API_KEY")
LOGFIRE_TOKEN = required_env("LOGFIRE_TOKEN")
WHOOP_CLIENT_ID = required_env("WHOOP_CLIENT_ID")
WHOOP_CLIENT_SECRET = required_env("WHOOP_CLIENT_SECRET")
WHOOP_TOKEN_ENCRYPTION_KEY = required_env("WHOOP_TOKEN_ENCRYPTION_KEY")

# Operational controls may be tuned without changing an image.
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.6-luna")
COACH_HISTORY_MAX_BATCHES = int(os.environ.get("COACH_HISTORY_MAX_BATCHES", "12"))
COACH_HISTORY_MAX_TOKENS = int(os.environ.get("COACH_HISTORY_MAX_TOKENS", "20000"))
COACH_MAX_MODEL_REQUESTS = int(os.environ.get("COACH_MAX_MODEL_REQUESTS", "6"))
COACH_MAX_TOOL_CALLS = int(os.environ.get("COACH_MAX_TOOL_CALLS", "12"))
COACH_MAX_INPUT_TOKENS = int(os.environ.get("COACH_MAX_INPUT_TOKENS", "40000"))
COACH_MAX_OUTPUT_TOKENS = int(os.environ.get("COACH_MAX_OUTPUT_TOKENS", "20000"))
COACH_MAX_INPUT_TOKENS_PER_REQUEST = int(
    os.environ.get("COACH_MAX_INPUT_TOKENS_PER_REQUEST", "20000")
)
COACH_TOOL_TIMEOUT_SECONDS = float(os.environ.get("COACH_TOOL_TIMEOUT_SECONDS", "10"))
COACH_STREAM_KEEPALIVE_SECONDS = float(
    os.environ.get("COACH_STREAM_KEEPALIVE_SECONDS", "15")
)
COACH_MAX_COST_USD = os.environ.get("COACH_MAX_COST_USD", "0.05")
COACH_LOGFIRE_ENABLED = env_bool("COACH_LOGFIRE_ENABLED", True)
COACH_LOGFIRE_CAPTURE_CONTENT = env_bool("COACH_LOGFIRE_CAPTURE_CONTENT", True)
COACH_LOGFIRE_CAPTURE_BINARY_CONTENT = env_bool(
    "COACH_LOGFIRE_CAPTURE_BINARY_CONTENT", True
)
COACH_LOGFIRE_CAPTURE_MODEL_REQUEST_PARAMETERS = env_bool(
    "COACH_LOGFIRE_CAPTURE_MODEL_REQUEST_PARAMETERS", True
)
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOGGING = build_logging(LOG_LEVEL)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
