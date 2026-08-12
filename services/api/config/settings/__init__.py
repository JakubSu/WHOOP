"""Select the Django settings module for the configured environment."""

import os

environment = os.environ.get("DJANGO_ENV", "local").strip().lower()

if environment == "local":
    from .local import *  # noqa: F403
elif environment == "production":
    from .production import *  # noqa: F403
else:
    raise RuntimeError('DJANGO_ENV must be either "local" or "production".')
