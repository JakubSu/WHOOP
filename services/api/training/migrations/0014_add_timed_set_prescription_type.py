from django.db import migrations, models


def migrate_weighted_or_set_timed_exercises(apps, schema_editor):
    Exercise = apps.get_model("training", "Exercise")
    WorkoutExercise = apps.get_model("training", "WorkoutExercise")

    timed_exercise_ids = Exercise.objects.filter(prescription_type="timed").values_list(
        "id", flat=True
    )
    exercise_ids_with_sets_reps_or_weight = set(
        WorkoutExercise.objects.filter(exercise_id__in=timed_exercise_ids)
        .exclude(sets=0)
        .values_list("exercise_id", flat=True)
    )
    exercise_ids_with_sets_reps_or_weight.update(
        WorkoutExercise.objects.filter(exercise_id__in=timed_exercise_ids)
        .exclude(reps=0)
        .values_list("exercise_id", flat=True)
    )
    exercise_ids_with_sets_reps_or_weight.update(
        WorkoutExercise.objects.filter(exercise_id__in=timed_exercise_ids)
        .exclude(weight__isnull=True)
        .values_list("exercise_id", flat=True)
    )
    Exercise.objects.filter(prescription_type="timed").exclude(
        default_sets=0, default_reps=0, default_weight__isnull=True
    ).update(prescription_type="timed_sets")
    Exercise.objects.filter(id__in=exercise_ids_with_sets_reps_or_weight).update(
        prescription_type="timed_sets"
    )


class Migration(migrations.Migration):
    dependencies = [("training", "0013_constrain_exercise_muscle_groups")]

    operations = [
        migrations.AlterField(
            model_name="exercise",
            name="prescription_type",
            field=models.CharField(
                choices=[
                    ("strength", "Strength"),
                    ("timed_sets", "Timed sets"),
                    ("timed", "Duration"),
                ],
                default="strength",
                max_length=32,
            ),
        ),
        migrations.RunPython(migrate_weighted_or_set_timed_exercises, migrations.RunPython.noop),
    ]
