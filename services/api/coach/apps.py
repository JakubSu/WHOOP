from django.apps import AppConfig


class CoachConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "coach"
    # Keep the historical migration identity and existing coaching_* tables.
    label = "coaching"
