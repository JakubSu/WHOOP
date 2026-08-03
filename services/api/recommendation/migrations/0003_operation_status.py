from django.db import migrations, models


def remove_effort_from_payloads(apps, schema_editor):
    RecommendationOperation = apps.get_model(
        "recommendation", "RecommendationOperation"
    )
    for operation in RecommendationOperation.objects.all():
        payload = operation.payload_json or {}
        changed = False
        if "effort" in payload:
            payload.pop("effort", None)
            changed = True
        changes = payload.get("changes")
        if isinstance(changes, dict) and "effort" in changes:
            changes.pop("effort", None)
            changed = True
        if changed:
            operation.payload_json = payload
            operation.save(update_fields=["payload_json"])


class Migration(migrations.Migration):
    dependencies = [
        ("recommendation", "0002_seed_demo_training_plan"),
        ("training", "0006_prescription_type_and_weight"),
    ]

    operations = [
        migrations.AlterField(
            model_name="recommendation",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("accepted", "Accepted"),
                    ("rejected", "Rejected"),
                    ("partial", "Partial"),
                    ("stale", "Stale"),
                    ("failed", "Failed"),
                ],
                default="pending",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="recommendationoperation",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("accepted", "Accepted"),
                    ("rejected", "Rejected"),
                    ("stale", "Stale"),
                    ("failed", "Failed"),
                ],
                default="pending",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="recommendationoperation",
            name="decided_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="recommendationoperation",
            name="applied_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(remove_effort_from_payloads, migrations.RunPython.noop),
    ]
