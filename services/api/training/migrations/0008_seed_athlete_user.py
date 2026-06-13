import uuid
from datetime import datetime

from django.db import migrations
from django.utils import timezone


ATHLETE_USER_ID = uuid.UUID("a559a75b-8c55-4a41-a2c8-bd15b9c2d8a3")
ATHLETE_CREATED_AT = timezone.make_aware(
    datetime.fromisoformat("2026-06-07 17:17:16.536262")
)
ATHLETE_UPDATED_AT = timezone.make_aware(
    datetime.fromisoformat("2026-06-11 14:52:48.946817")
)


def seed_athlete_user(apps, schema_editor):
    User = apps.get_model("users", "User")

    User.objects.update_or_create(
        id=ATHLETE_USER_ID,
        defaults={
            "password": "pbkdf2_sha256$1000000$zDg8MsM1ie5PpDwYtjykUf$QTuXHtfb60DMMsmO+Pwo1X6EMl1Gm/mHdUSgeILY1UI=",  # test user
            "last_login": None,
            "is_superuser": False,
            "email": "athlete@example.com",
            "display_name": "Athlete",
            "whoop_user_id": "",
            "is_active": True,
            "is_staff": False,
        },
    )
    User.objects.filter(id=ATHLETE_USER_ID).update(
        created_at=ATHLETE_CREATED_AT,
        updated_at=ATHLETE_UPDATED_AT,
    )


def remove_athlete_user(apps, schema_editor):
    User = apps.get_model("users", "User")
    User.objects.filter(id=ATHLETE_USER_ID).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
        ("training", "0007_seed_push_lower_plan_and_exercises"),
    ]

    operations = [
        migrations.RunPython(seed_athlete_user, remove_athlete_user),
    ]
