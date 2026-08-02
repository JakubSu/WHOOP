# ruff: noqa: RUF012
# Generated manually for patch-based workout recommendations.

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Recommendation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("user_id", models.CharField(db_index=True, max_length=200)),
                ("workout_id", models.UUIDField(db_index=True)),
                ("snapshot_version", models.CharField(max_length=200)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("accepted", "Accepted"), ("rejected", "Rejected"), ("stale", "Stale"), ("failed", "Failed")], default="pending", max_length=32)),
                ("summary", models.TextField(blank=True, default="")),
                ("reason", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="RecommendationOperation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("sequence", models.PositiveIntegerField()),
                ("operation_type", models.CharField(choices=[("replace_exercise", "Replace exercise"), ("update_exercise", "Update exercise"), ("remove_exercise", "Remove exercise"), ("add_exercise", "Add exercise")], max_length=64)),
                ("payload_json", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("recommendation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="operations", to="recommendation.recommendation")),
            ],
            options={
                "ordering": ["sequence"],
            },
        ),
        migrations.AddIndex(
            model_name="recommendation",
            index=models.Index(fields=["user_id", "workout_id"], name="recommendat_user_id_397991_idx"),
        ),
        migrations.AddIndex(
            model_name="recommendation",
            index=models.Index(fields=["user_id", "status"], name="recommendat_user_id_f8bf4c_idx"),
        ),
        migrations.AddConstraint(
            model_name="recommendationoperation",
            constraint=models.UniqueConstraint(fields=("recommendation", "sequence"), name="unique_recommendation_operation_sequence"),
        ),
    ]
