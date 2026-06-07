import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="WhoopConnection",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("user_id", models.CharField(max_length=64, unique=True)),
                ("whoop_user_id", models.CharField(max_length=64)),
                ("access_token_encrypted", models.TextField()),
                ("refresh_token_encrypted", models.TextField(blank=True, default="")),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("scopes", models.TextField(blank=True, default="")),
                ("connected_at", models.DateTimeField(auto_now_add=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-connected_at"],
            },
        ),
        migrations.CreateModel(
            name="WhoopSnapshot",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("user_id", models.CharField(max_length=64)),
                ("snapshot_date", models.DateField()),
                ("recovery_score", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                (
                    "sleep_performance_percent",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
                ),
                ("day_strain", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ("hrv_rmssd_milli", models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ("resting_heart_rate", models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ("sleep_duration_minutes", models.PositiveIntegerField(blank=True, null=True)),
                ("recent_workout_count", models.PositiveIntegerField(default=0)),
                ("raw_payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-snapshot_date", "-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="whoopsnapshot",
            index=models.Index(fields=["user_id", "snapshot_date"], name="whoop_whoop_user_id_740e56_idx"),
        ),
    ]
