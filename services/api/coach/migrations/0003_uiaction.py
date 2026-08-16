import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("coaching", "0002_conversation_api")]

    operations = [
        migrations.CreateModel(
            name="UiAction",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("type", models.CharField(max_length=64)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("resolved", "Resolved"), ("dismissed", "Dismissed")], default="pending", max_length=16)),
                ("payload", models.JSONField(default=dict)),
                ("resolution", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("message", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ui_actions", to="coaching.coachmessage")),
            ],
        ),
        migrations.AddIndex(
            model_name="uiaction",
            index=models.Index(fields=["message", "status"], name="coach_uiaction_msg_status_idx"),
        ),
    ]
