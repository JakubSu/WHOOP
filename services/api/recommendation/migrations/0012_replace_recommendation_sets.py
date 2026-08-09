from django.db import migrations, models
from django.db.models import Q
from django.utils import timezone


def supersede_duplicate_active_recommendations(apps, schema_editor):
    """Keeps the newest active proposal before enforcing one per conversation."""

    recommendation_model = apps.get_model("recommendation", "Recommendation")
    operation_model = apps.get_model("recommendation", "RecommendationOperation")
    database = schema_editor.connection.alias
    now = timezone.now()
    conversation_ids = (
        recommendation_model.objects.using(database)
        .filter(status="active", conversation_id__isnull=False)
        .values_list("conversation_id", flat=True)
        .distinct()
    )
    for conversation_id in conversation_ids:
        active = list(
            recommendation_model.objects.using(database)
            .filter(conversation_id=conversation_id, status="active")
            .order_by("-created_at", "-id")
        )
        for recommendation in active[1:]:
            recommendation.status = "superseded"
            recommendation.superseded_at = now
            recommendation.save(using=database, update_fields=["status", "superseded_at"])
            operation_model.objects.using(database).filter(
                recommendation_id=recommendation.id, status="pending"
            ).update(status="stale", resolved_at=now, updated_at=now)


class Migration(migrations.Migration):
    dependencies = [("recommendation", "0011_ai_recommendation_provenance")]

    operations = [
        migrations.AddField(
            model_name="recommendation",
            name="replaced_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name="replaces",
                to="recommendation.recommendation",
            ),
        ),
        migrations.AddField(
            model_name="recommendation",
            name="superseded_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="recommendation",
            name="presentation_snapshot",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name="recommendation",
            name="status",
            field=models.CharField(
                choices=[
                    ("active", "Active"),
                    ("completed", "Completed"),
                    ("superseded", "Superseded"),
                    ("expired", "Expired"),
                ],
                db_index=True,
                default="active",
                max_length=16,
            ),
        ),
        migrations.RunPython(
            supersede_duplicate_active_recommendations, migrations.RunPython.noop
        ),
        migrations.AddConstraint(
            model_name="recommendation",
            constraint=models.UniqueConstraint(
                condition=Q(status="active", conversation__isnull=False),
                fields=("conversation",),
                name="rec_one_active_per_conversation",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="recommendationoperation",
            name="rec_op_not_self_superseding",
        ),
        migrations.RemoveField(model_name="recommendationoperation", name="conversation"),
        migrations.RemoveField(model_name="recommendationoperation", name="message"),
        migrations.RemoveField(model_name="recommendationoperation", name="supersedes"),
        migrations.AlterField(
            model_name="recommendationoperation",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("accepted", "Accepted"),
                    ("rejected", "Rejected"),
                    ("stale", "Stale"),
                ],
                db_index=True,
                default="pending",
                max_length=16,
            ),
        ),
    ]
