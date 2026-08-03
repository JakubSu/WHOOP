import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("coaching", "0001_initial"),
        ("recommendation", "0006_delete_recommendation_operation"),
    ]
    operations = [
        migrations.RunSQL(
            "DELETE FROM recommendation_recommendation", migrations.RunSQL.noop
        ),
        migrations.RemoveField(model_name="recommendation", name="user_id"),
        migrations.RemoveField(model_name="recommendation", name="workout_id"),
        migrations.RemoveField(model_name="recommendation", name="snapshot_version"),
        migrations.RemoveField(model_name="recommendation", name="status"),
        migrations.RemoveField(model_name="recommendation", name="operation_type"),
        migrations.RemoveField(model_name="recommendation", name="payload_json"),
        migrations.RemoveField(model_name="recommendation", name="source"),
        migrations.RemoveField(
            model_name="recommendation", name="coach_conversation_id"
        ),
        migrations.RemoveField(model_name="recommendation", name="coach_message_id"),
        migrations.AlterField(
            model_name="recommendation",
            name="summary",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
        migrations.AddField(
            model_name="recommendation",
            name="conversation",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="recommendations",
                to="coaching.coachconversation",
            ),
        ),
        migrations.AddField(
            model_name="recommendation",
            name="coach_message",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="recommendations",
                to="coaching.coachmessage",
            ),
        ),
        migrations.AddField(
            model_name="recommendation",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="recommendations",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name="RecommendationOperation",
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
                (
                    "operation_type",
                    models.CharField(
                        choices=[
                            ("add_workout", "Add workout"),
                            ("update_workout", "Update workout"),
                            ("remove_workout", "Remove workout"),
                            ("add_exercise", "Add exercise"),
                            ("update_exercise", "Update exercise"),
                            ("remove_exercise", "Remove exercise"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("accepted", "Accepted"),
                            ("rejected", "Rejected"),
                            ("superseded", "Superseded"),
                            ("stale", "Stale"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("display_text", models.TextField(blank=True, default="")),
                ("reason", models.TextField(blank=True, default="")),
                ("payload", models.JSONField()),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("daily_recommendation", "Daily recommendation"),
                            ("coach_chat", "Coach chat"),
                        ],
                        default="daily_recommendation",
                        max_length=64,
                    ),
                ),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "updated_by",
                    models.CharField(
                        choices=[
                            ("user", "User"),
                            ("coach_chat", "Coach chat"),
                            ("system", "System"),
                        ],
                        default="coach_chat",
                        max_length=32,
                    ),
                ),
                (
                    "created_by_message",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_recommendation_operations",
                        to="coaching.coachmessage",
                    ),
                ),
                (
                    "recommendation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="operations",
                        to="recommendation.recommendation",
                    ),
                ),
                (
                    "supersedes",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="superseded_by",
                        to="recommendation.recommendationoperation",
                    ),
                ),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.AddIndex(
            model_name="recommendation",
            index=models.Index(
                fields=["user", "created_at"], name="rec_user_created_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="recommendation",
            index=models.Index(
                fields=["conversation", "created_at"], name="rec_conversation_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="recommendationoperation",
            index=models.Index(
                fields=["recommendation", "status"], name="rec_op_pending_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="recommendationoperation",
            index=models.Index(
                fields=["status", "created_at"], name="rec_op_status_idx"
            ),
        ),
    ]
