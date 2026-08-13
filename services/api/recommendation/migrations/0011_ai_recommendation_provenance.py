from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [("recommendation", "0010_link_operations_to_coach_messages")]

    operations = [
        migrations.AddField(
            model_name="recommendation",
            name="expired_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="recommendation",
            name="run_id",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="recommendation",
            name="status",
            field=models.CharField(
                choices=[("active", "Active"), ("expired", "Expired")],
                db_index=True,
                default="active",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="recommendation",
            name="tool_call_id",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddIndex(
            model_name="recommendation",
            index=models.Index(fields=["run_id", "status"], name="rec_run_status_idx"),
        ),
        migrations.AddConstraint(
            model_name="recommendation",
            constraint=models.UniqueConstraint(
                condition=Q(run_id__isnull=False, tool_call_id__isnull=False),
                fields=("run_id", "tool_call_id"),
                name="rec_run_tool_call_unique",
            ),
        ),
    ]
