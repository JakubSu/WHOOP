import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CoachConversation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("user_id", models.CharField(db_index=True, max_length=200)),
                (
                    "page_type",
                    models.CharField(
                        choices=[
                            ("today_workout", "Today workout"),
                            ("workout", "Workout"),
                            ("training_plan", "Training plan"),
                            ("recovery", "Recovery"),
                        ],
                        max_length=32,
                    ),
                ),
                ("context_id", models.CharField(blank=True, default="", max_length=200)),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Active"), ("archived", "Archived")],
                        default="active",
                        max_length=32,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("last_message_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "ordering": ["-last_message_at", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="CoachMessage",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "role",
                    models.CharField(
                        choices=[("user", "User"), ("assistant", "Assistant")],
                        max_length=32,
                    ),
                ),
                ("content", models.TextField()),
                ("metadata_json", models.JSONField(default=dict)),
                ("recommendation_id", models.UUIDField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "conversation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="coaching.coachconversation",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="coachconversation",
            index=models.Index(fields=["user_id", "page_type", "context_id", "status"], name="coach_conv_scope_idx"),
        ),
        migrations.AddIndex(
            model_name="coachconversation",
            index=models.Index(fields=["user_id", "last_message_at"], name="coach_conv_last_msg_idx"),
        ),
        migrations.AddIndex(
            model_name="coachmessage",
            index=models.Index(fields=["conversation", "created_at"], name="coach_msg_conversation_idx"),
        ),
    ]
