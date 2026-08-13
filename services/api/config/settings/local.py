"""Local-development settings. Secrets are read from services/api/.env."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from .base import *

ENVIRONMENT = "local"
DEBUG = env_bool("DEBUG", True)
DATABASES = (
    postgres_database()
    if os.environ.get("DATABASE_ENGINE") == "postgres"
    else {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
)
LOGGING = build_logging(LOG_LEVEL)
