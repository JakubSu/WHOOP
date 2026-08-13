from django.db import migrations, models
from django.db.models import Q
from django.utils import timezone


def supersede_duplicate_active_recommendations_per_user(apps, schema_editor):
    """Keeps the newest active proposal before enforcing one per user."""

    recommendation_model = apps.get_model("recommendation", "Recommendation")
    operation_model = apps.get_model("recommendation", "RecommendationOperation")
    database = schema_editor.connection.alias
    now = timezone.now()
    user_ids = (
        recommendation_model.objects.using(database)
        .filter(status="active")
        .values_list("user_id", flat=True)
        .distinct()
    )
    for user_id in user_ids:
        active = list(
            recommendation_model.objects.using(database)
            .filter(user_id=user_id, status="active")
            .order_by("-created_at", "-id")
        )
        for recommendation in active[1:]:
            recommendation.status = "superseded"
            recommendation.superseded_at = now
            recommendation.save(
                using=database, update_fields=["status", "superseded_at"]
            )
            operation_model.objects.using(database).filter(
                recommendation_id=recommendation.id, status="pending"
            ).update(status="stale", resolved_at=now, updated_at=now)


class Migration(migrations.Migration):
    dependencies = [("recommendation", "0014_rename_presentation_snapshot")]

    operations = [
        migrations.RemoveConstraint(
            model_name="recommendation",
            name="rec_one_active_per_conversation",
        ),
        migrations.RunPython(
            supersede_duplicate_active_recommendations_per_user,
            migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="recommendation",
            constraint=models.UniqueConstraint(
                fields=("user",),
                condition=Q(status="active"),
                name="rec_one_active_per_user",
            ),
        ),
    ]
