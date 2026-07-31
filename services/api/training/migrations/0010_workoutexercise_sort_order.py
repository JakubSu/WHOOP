from django.db import migrations, models


def seed_sort_order(apps, schema_editor):
    WorkoutExercise = apps.get_model("training", "WorkoutExercise")

    current_workout = object()
    exercise_order = 0
    for workout_exercise in WorkoutExercise.objects.order_by(
        "workout_id", "created_at", "exercise__name"
    ):
        workout_key = workout_exercise.workout_id
        if workout_key != current_workout:
            current_workout = workout_key
            exercise_order = 1
        else:
            exercise_order += 1
        workout_exercise.sort_order = exercise_order
        workout_exercise.save(update_fields=["sort_order"])


class Migration(migrations.Migration):

    dependencies = [  # noqa: RUF012
        ("training", "0009_plan_constraints_and_workout_ordering"),
    ]

    operations = [  # noqa: RUF012
        migrations.AddField(
            model_name="workoutexercise",
            name="sort_order",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(seed_sort_order, migrations.RunPython.noop),
        migrations.AlterModelOptions(
            name="workout",
            options={"ordering": ["date", "name"]},
        ),
        migrations.AlterModelOptions(
            name="workoutexercise",
            options={"ordering": ["workout", "sort_order", "created_at", "exercise__name"]},
        ),
    ]
