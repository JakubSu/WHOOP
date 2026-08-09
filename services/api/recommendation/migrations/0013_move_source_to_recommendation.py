from django.db import migrations, models


def copy_operation_source_to_recommendation(apps, schema_editor):
    """Copies the shared legacy operation origin to its recommendation parent."""

    recommendation_model = apps.get_model("recommendation", "Recommendation")
    operation_model = apps.get_model("recommendation", "RecommendationOperation")
    database = schema_editor.connection.alias
    for recommendation in recommendation_model.objects.using(database).iterator():
        source = (
            operation_model.objects.using(database)
            .filter(recommendation_id=recommendation.id)
            .order_by("created_at", "id")
            .values_list("source", flat=True)
            .first()
        )
        if source:
            recommendation.source = source
            recommendation.save(using=database, update_fields=["source"])


class Migration(migrations.Migration):
    dependencies = [("recommendation", "0012_replace_recommendation_sets")]

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
        migrations.RunPython(
            copy_operation_source_to_recommendation, migrations.RunPython.noop
        ),
        migrations.RemoveField(model_name="recommendationoperation", name="source"),
        migrations.RemoveField(
            model_name="recommendationoperation",
            name="updated_by",
        ),
    ]
