import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("whoop", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="WhoopOAuthState",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("state", models.CharField(max_length=255, unique=True)),
                ("user_id", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="whoopoauthstate",
            index=models.Index(fields=["state"], name="whoop_whoop_state_c46967_idx"),
        ),
        migrations.AddIndex(
            model_name="whoopoauthstate",
            index=models.Index(
                fields=["user_id", "created_at"], name="whoop_whoop_user_id_717adb_idx"
            ),
        ),
    ]
