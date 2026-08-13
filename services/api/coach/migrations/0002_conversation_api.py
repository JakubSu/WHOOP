import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.migrations.exceptions import IrreversibleError


def discard_legacy_coach_data(apps, schema_editor):
    operation_model = apps.get_model("recommendation", "RecommendationOperation")
    recommendation_model = apps.get_model("recommendation", "Recommendation")
    message_model = apps.get_model("coaching", "CoachMessage")
    conversation_model = apps.get_model("coaching", "CoachConversation")
    database = schema_editor.connection.alias

    # V1 chat and proposal data is intentionally incompatible with the new
    # conversation contract. Detach the recommendation ledger before deleting
    # chat rows; applied workout changes and recommendation history survive.
    operation_model.objects.using(database).update(created_by_message_id=None)
    recommendation_model.objects.using(database).update(
        conversation_id=None,
        coach_message_id=None,
    )
    message_model.objects.using(database).all().delete()
    conversation_model.objects.using(database).all().delete()


def legacy_coach_data_cannot_be_restored(apps, schema_editor):
    raise IrreversibleError("Discarded legacy coach conversations cannot be restored.")


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("coaching", "0001_initial"),
        ("recommendation", "0009_prepare_coach_reset"),
    ]

    operations = [
        migrations.RunPython(
            discard_legacy_coach_data,
            legacy_coach_data_cannot_be_restored,
        ),
        migrations.RemoveIndex(
            model_name="coachconversation", name="coach_conv_scope_idx"
        ),
        migrations.RemoveIndex(
            model_name="coachconversation", name="coach_conv_last_msg_idx"
        ),
        migrations.RemoveIndex(
            model_name="coachmessage", name="coach_msg_conversation_idx"
        ),
        migrations.RemoveField(model_name="coachconversation", name="page_type"),
        migrations.RemoveField(model_name="coachconversation", name="context_id"),
        migrations.RemoveField(model_name="coachconversation", name="status"),
        migrations.RemoveField(model_name="coachconversation", name="last_message_at"),
        migrations.RemoveField(model_name="coachmessage", name="metadata_json"),
        migrations.RemoveField(model_name="coachmessage", name="recommendation_id"),
        # `user_id` began as a CharField with db_index=True. PostgreSQL creates
        # this extra pattern-ops index for text columns, but it cannot survive
        # the UUID conversion below. Django does not remove it because the
        # target ForeignKey is indexed as well.
        migrations.RunSQL(
            sql=(
                "DROP INDEX IF EXISTS "
                "coaching_coachconversation_user_id_fd228c8b_like"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RenameField(
            model_name="coachconversation", old_name="user_id", new_name="user"
        ),
        migrations.AlterField(
            model_name="coachconversation",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="coach_conversations",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="coachconversation",
            name="title",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="coachmessage",
            name="ai_message_batch",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="coachmessage",
            name="activity_log",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterModelOptions(
            name="coachconversation", options={"ordering": ["-updated_at", "-id"]}
        ),
        migrations.AlterModelOptions(
            name="coachmessage", options={"ordering": ["created_at", "id"]}
        ),
        migrations.AddIndex(
            model_name="coachconversation",
            index=models.Index(
                fields=["user", "updated_at"], name="coach_conv_user_updated_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="coachmessage",
            index=models.Index(
                fields=["conversation", "created_at", "id"],
                name="coach_msg_conv_created_idx",
            ),
        ),
    ]
