# ruff: noqa: RUF012

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("recommendation", "0003_operation_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="recommendation",
            name="source",
            field=models.CharField(
                choices=[
                    ("daily_recommendation", "Daily recommendation"),
                    ("coach_chat", "Coach chat"),
                ],
                default="daily_recommendation",
                max_length=64,
            ),
        ),
        migrations.AddField(
            model_name="recommendation",
            name="coach_conversation_id",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="recommendation",
            name="coach_message_id",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
    ]
