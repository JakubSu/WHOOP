from django.db import migrations, models

TIMED_EXERCISE_NAMES = {
    "bike intervals",
    "breathing walk",
    "plank",
    "rowing intervals",
    "wall sit",
    "zone 2 run",
}


def migrate_prescriptions(apps, schema_editor):
    Exercise = apps.get_model("training", "Exercise")
    WorkoutExercise = apps.get_model("training", "WorkoutExercise")

    for exercise in Exercise.objects.all():
        is_timed = (
            exercise.default_time > 0 or exercise.name.lower() in TIMED_EXERCISE_NAMES
        )
        exercise.prescription_type = "timed" if is_timed else "strength"
        exercise.save(update_fields=["prescription_type"])

    for workout_exercise in WorkoutExercise.objects.select_related("exercise"):
        effort = getattr(workout_exercise, "effort", "")
        if effort:
            prefix = f"Effort: {effort}."
            workout_exercise.note = f"{workout_exercise.note}\n{prefix}".strip()

        if workout_exercise.exercise.prescription_type == "timed":
            workout_exercise.sets = 0
            workout_exercise.reps = 0
            workout_exercise.weight = None
            workout_exercise.weight_unit = "lb"
        else:
            workout_exercise.time = 0
            workout_exercise.weight_unit = "lb"

        workout_exercise.save(
            update_fields=["sets", "reps", "time", "weight", "weight_unit", "note"]
        )


def reverse_prescriptions(apps, schema_editor):
    WorkoutExercise = apps.get_model("training", "WorkoutExercise")
    WorkoutExercise.objects.update(effort="")


class Migration(migrations.Migration):
    dependencies = [
        ("training", "0005_minimal_training_schema"),
        ("recommendation", "0002_seed_demo_training_plan"),
    ]

    operations = [
        migrations.AddField(
            model_name="exercise",
            name="prescription_type",
            field=models.CharField(
                choices=[("strength", "Strength"), ("timed", "Timed")],
                default="strength",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="workoutexercise",
            name="weight",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=7,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="workoutexercise",
            name="weight_unit",
            field=models.CharField(default="lb", max_length=16),
        ),
        migrations.RunPython(migrate_prescriptions, reverse_prescriptions),
        migrations.RemoveField(
            model_name="workoutexercise",
            name="effort",
        ),
    ]
