import os

from django.core.asgi import get_asgi_application

from ai.implementations.pydantic_coach.observability import (
    configure_observability_from_settings,
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
configure_observability_from_settings()
