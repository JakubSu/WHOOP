from django.db import migrations


def migrate_operation_payloads(apps, schema_editor):
    """Preserves pending ledgers while replacing their public contract shape."""

    operation_model = apps.get_model("recommendation", "RecommendationOperation")
    database = schema_editor.connection.alias
    for operation in operation_model.objects.using(database).all().iterator():
        payload = operation.payload
        if operation.operation_type == "add_exercise" and "workout" not in payload:
            workout_id = payload.pop("workout_id", None)
            temporary_workout_id = payload.pop("temporary_workout_id", None)
            payload["workout"] = (
                {"kind": "existing", "workout_id": workout_id}
                if workout_id is not None
                else {"kind": "new", "temporary_id": temporary_workout_id}
            )
            exercise = payload.pop("exercise", {})
            payload["exercise_id"] = exercise.get("id")
            prescription = payload.get("prescription", {})
            if "type" not in prescription:
                seconds = prescription.pop("time", 0)
                if seconds:
                    prescription["type"] = "time"
                    prescription["seconds"] = seconds
                    prescription.pop("reps", None)
                    prescription.pop("weight", None)
                    prescription.pop("weight_unit", None)
                else:
                    prescription["type"] = "reps"
            payload["prescription"] = prescription
        elif operation.operation_type == "update_exercise":
            target_workout_id = payload.pop("workout_id", None)
            if target_workout_id is not None:
                payload["target_workout_id"] = target_workout_id
        operation.payload = payload
        operation.save(using=database, update_fields=["payload"])


class Migration(migrations.Migration):
    dependencies = [("recommendation", "0015_one_active_recommendation_per_user")]

    operations = [
        migrations.RunPython(migrate_operation_payloads, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="recommendation",
            name="reason",
        ),
    ]
