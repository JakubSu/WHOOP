# ruff: noqa: RUF012

from django.db import migrations, models


def copy_first_operation_to_recommendation(apps, schema_editor):
    Recommendation = apps.get_model("recommendation", "Recommendation")
    RecommendationOperation = apps.get_model("recommendation", "RecommendationOperation")

    status_map = {
        "accepted": "applied",
        "partial": "failed",
    }
    for recommendation in Recommendation.objects.all():
        mapped_status = status_map.get(recommendation.status)
        update_fields = []
        if mapped_status:
            recommendation.status = mapped_status
            update_fields.append("status")

        first_operation = (
            RecommendationOperation.objects.filter(recommendation=recommendation)
            .order_by("sequence")
            .first()
        )
        if first_operation is not None:
            recommendation.operation_type = first_operation.operation_type
            recommendation.payload_json = first_operation.payload_json
            update_fields.extend(["operation_type", "payload_json"])

        if update_fields:
            recommendation.save(update_fields=update_fields)


class Migration(migrations.Migration):

    dependencies = [
        ("recommendation", "0004_coach_source_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="recommendation",
            name="operation_type",
            field=models.CharField(
                choices=[
                    ("add_exercise", "Add exercise"),
                    ("remove_exercise", "Remove exercise"),
                    ("replace_exercise", "Replace exercise"),
                    ("update_exercise", "Update exercise"),
                    ("move_exercise", "Move exercise"),
                    ("add_workout", "Add workout"),
                    ("remove_workout", "Remove workout"),
                    ("update_workout", "Update workout"),
                    ("revise_workout", "Revise workout"),
                ],
                default="update_exercise",
                max_length=64,
            ),
        ),
        migrations.AddField(
            model_name="recommendation",
            name="payload_json",
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name="recommendation",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("applied", "Applied"),
                    ("rejected", "Rejected"),
                    ("stale", "Stale"),
                    ("failed", "Failed"),
                ],
                default="pending",
                max_length=32,
            ),
        ),
        migrations.RunPython(
            copy_first_operation_to_recommendation,
            migrations.RunPython.noop,
        ),
    ]
