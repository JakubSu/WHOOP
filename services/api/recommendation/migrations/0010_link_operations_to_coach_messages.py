import django.db.models.deletion
from django.db import migrations, models


def backfill_operation_conversations(apps, schema_editor):
    operation_model = apps.get_model("recommendation", "RecommendationOperation")
    database = schema_editor.connection.alias
    for operation in (
        operation_model.objects.using(database)
        .select_related("recommendation")
        .iterator()
    ):
        operation.conversation_id = operation.recommendation.conversation_id
        operation.save(using=database, update_fields=["conversation"])


class Migration(migrations.Migration):
    dependencies = [
        ("coaching", "0002_conversation_api"),
        ("recommendation", "0009_prepare_coach_reset"),
    ]

    operations = [
        migrations.RenameField(
            model_name="recommendationoperation",
            old_name="created_by_message",
            new_name="message",
        ),
        migrations.AlterField(
            model_name="recommendationoperation",
            name="message",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="recommendation_operations",
                to="coaching.coachmessage",
            ),
        ),
        migrations.AddField(
            model_name="recommendationoperation",
            name="conversation",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="recommendation_operations",
                to="coaching.coachconversation",
            ),
        ),
        migrations.RunPython(
            backfill_operation_conversations, migrations.RunPython.noop
        ),
    ]
