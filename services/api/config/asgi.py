import os

from django.core.asgi import get_asgi_application

from ai.implementations.pydantic_coach.observability import (
    configure_observability_from_settings,
)
from ai.runner import initialize_coach_runner

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
initialize_coach_runner()
configure_observability_from_settings()
