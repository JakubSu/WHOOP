# ruff: noqa: RUF012

import uuid

from django.contrib.auth.hashers import make_password
from django.db import migrations

DEMO_USER_ID = uuid.UUID("7ed6ecb0-7a0a-4e10-8f30-31d3a0b45f10")
DEMO_PLAN_ID = uuid.UUID("ebf1c7b7-10f5-4d3e-b6fb-22c10d5620d1")
DEMO_RECOMMENDATION_ID = uuid.UUID("a302f82a-0f82-4ce9-8688-8df1b03c84cb")
DEMO_OPERATION_ID = uuid.UUID("fd2699a2-ad18-47c9-92a7-e797b7057430")

EXERCISE_IDS = {
    "Goblet Squat": uuid.UUID("5df97d62-b95b-4633-9d8e-5e5fe6912ff0"),
    "Romanian Deadlift": uuid.UUID("39941b1c-06e7-4e41-8f22-070db8c4f89d"),
    "Walking Lunge": uuid.UUID("f5b69554-f278-4272-bfd7-23ac38035dbd"),
    "Plank": uuid.UUID("6ac0a052-695f-4c87-8108-e6bd70c89654"),
    "Bench Press": uuid.UUID("0a25de39-5d82-4bbf-b1e8-b71a8e99e140"),
    "One Arm Row": uuid.UUID("d495d408-7b1c-4a8c-872a-bf34f78f2d24"),
    "Overhead Press": uuid.UUID("a67af0cc-519b-41a9-8c7d-a7396097ac0b"),
    "Lat Pulldown": uuid.UUID("65f72bcb-63d8-4f3b-953d-151f19f0364f"),
    "Bike Intervals": uuid.UUID("76ef4fae-9f0a-475a-a1ab-1d4e9bdbf1af"),
    "Kettlebell Swing": uuid.UUID("a8742e25-6cf4-4080-a6ec-03c97dca4a97"),
    "Push Up": uuid.UUID("3ea674af-d516-47e8-9a41-f427f4eaa56e"),
    "Dead Bug": uuid.UUID("43f61a0c-4678-4740-bd4a-f792b5f6dd65"),
    "Split Squat": uuid.UUID("9b954879-32c0-46c0-93be-05bc6689c708"),
    "Incline Dumbbell Press": uuid.UUID("4f553781-b9fd-4967-a2a4-0aab05d3f951"),
    "Cable Row": uuid.UUID("3018d9d9-8d1a-4130-9c4b-85e69a75ff5a"),
}

WORKOUT_IDS = {
    "Lower Body Strength": uuid.UUID("1d105ed9-3562-4301-94ff-e78e06f0a1ed"),
    "Upper Body Strength": uuid.UUID("cb9a98b2-4f2f-46d0-b2ab-8b725335ccce"),
    "Conditioning Reset": uuid.UUID("70b339b1-3f91-4ac2-94d0-bf312fc8d276"),
}

WORKOUT_EXERCISE_IDS = {
    ("Lower Body Strength", "Goblet Squat"): uuid.UUID("74ba1fd6-faa2-453b-b218-f43240369a88"),
    ("Lower Body Strength", "Romanian Deadlift"): uuid.UUID("ac337698-9f89-4d74-a251-b27a8cc6b12a"),
    ("Lower Body Strength", "Walking Lunge"): uuid.UUID("0b7e69a9-d684-4ed3-9ac7-dd143c6d7563"),
    ("Lower Body Strength", "Split Squat"): uuid.UUID("f18961a3-d903-4e73-99d4-a9b7dd76077f"),
    ("Lower Body Strength", "Plank"): uuid.UUID("2dfc941e-54f2-4801-bd84-b58ae3fbdac7"),
    ("Upper Body Strength", "Bench Press"): uuid.UUID("8e619579-eb12-41a8-9728-ec8b660b6f70"),
    ("Upper Body Strength", "One Arm Row"): uuid.UUID("589d1039-a1b7-43f9-b5be-373ef69bdc02"),
    ("Upper Body Strength", "Overhead Press"): uuid.UUID("d639883d-47eb-4fb1-90f7-9f8474a61d0e"),
    ("Upper Body Strength", "Lat Pulldown"): uuid.UUID("c1c5c338-6b5c-4740-a69e-97b06bf29d40"),
    ("Conditioning Reset", "Bike Intervals"): uuid.UUID("8445d22c-344f-4087-a8bb-05c41460ff70"),
    ("Conditioning Reset", "Kettlebell Swing"): uuid.UUID("04346949-ad99-46df-ae5b-a043f7d16cfc"),
    ("Conditioning Reset", "Push Up"): uuid.UUID("69e49c78-3525-4c3f-b696-b35fa9339021"),
    ("Conditioning Reset", "Dead Bug"): uuid.UUID("5a98eba2-97bd-4d80-aa61-a712bb513cd8"),
    ("Conditioning Reset", "Incline Dumbbell Press"): uuid.UUID("1854d618-a058-4841-ad8a-904ba7fc242a"),
    ("Conditioning Reset", "Cable Row"): uuid.UUID("c11018af-1273-49ec-a7c3-e1c0a4a60ae3"),
}


def seed_demo_training_plan(apps, schema_editor):
    User = apps.get_model("users", "User")
    Exercise = apps.get_model("training", "Exercise")
    TrainingPlan = apps.get_model("training", "TrainingPlan")
    Workout = apps.get_model("training", "Workout")
    WorkoutExercise = apps.get_model("training", "WorkoutExercise")
    Recommendation = apps.get_model("recommendation", "Recommendation")
    RecommendationOperation = apps.get_model("recommendation", "RecommendationOperation")

    user, _ = User.objects.update_or_create(
        id=DEMO_USER_ID,
        defaults={
            "email": "demo.ai-coach@example.com",
            "display_name": "Demo Athlete",
            "password": make_password("demo-password"),
            "is_active": True,
            "is_staff": False,
            "is_superuser": False,
        },
    )

    plan, _ = TrainingPlan.objects.update_or_create(
        id=DEMO_PLAN_ID,
        defaults={
            "user_id": str(user.id),
            "name": "WHOOP-Aware Strength Block",
            "start_date": "2026-06-15",
            "end_date": "2026-07-05",
        },
    )

    exercise_defaults = {
        "Goblet Squat": (4, 10, "Legs", 0, "Control the eccentric."),
        "Romanian Deadlift": (3, 8, "Posterior Chain", 0, "Keep the load moderate."),
        "Walking Lunge": (3, 12, "Legs", 0, "Count reps per side."),
        "Plank": (3, 0, "Core", 45, "Hold strong posture."),
        "Bench Press": (4, 8, "Chest", 0, "Leave two reps in reserve."),
        "One Arm Row": (4, 10, "Back", 0, "Pause at the top."),
        "Overhead Press": (3, 8, "Shoulders", 0, "Brace before each rep."),
        "Lat Pulldown": (3, 12, "Back", 0, "Full range of motion."),
        "Bike Intervals": (6, 0, "Conditioning", 60, "One minute hard, one minute easy."),
        "Kettlebell Swing": (4, 15, "Posterior Chain", 0, "Snap the hips."),
        "Push Up": (3, 15, "Chest", 0, "Scale to clean reps."),
        "Dead Bug": (3, 10, "Core", 0, "Slow alternating sides."),
        "Split Squat": (3, 10, "Legs", 0, "Stay tall."),
        "Incline Dumbbell Press": (3, 10, "Chest", 0, "Smooth tempo."),
        "Cable Row": (3, 12, "Back", 0, "Squeeze shoulder blades."),
    }
    exercises = {}
    for name, defaults in exercise_defaults.items():
        default_sets, default_reps, muscle_group, default_time, notes = defaults
        exercise, _ = Exercise.objects.update_or_create(
            id=EXERCISE_IDS[name],
            defaults={
                "user_id": str(user.id),
                "name": name,
                "default_sets": default_sets,
                "default_reps": default_reps,
                "muscle_group": muscle_group,
                "default_time": default_time,
                "notes": notes,
            },
        )
        exercises[name] = exercise

    workout_specs = [
        (
            "Lower Body Strength",
            "2026-06-15",
            55,
            [
                ("Goblet Squat", 4, 10, 0, "moderate", "Main strength lift."),
                ("Romanian Deadlift", 3, 8, 0, "moderate", "Keep hamstrings loaded."),
                ("Walking Lunge", 3, 12, 0, "moderate", "Per side."),
                ("Split Squat", 3, 10, 0, "easy", "Unilateral accessory."),
                ("Plank", 3, 0, 45, "steady", "Brace and breathe."),
            ],
        ),
        (
            "Upper Body Strength",
            "2026-06-17",
            50,
            [
                ("Bench Press", 4, 8, 0, "moderate", "Primary press."),
                ("One Arm Row", 4, 10, 0, "moderate", "Balance pressing volume."),
                ("Overhead Press", 3, 8, 0, "moderate", "Strict reps."),
                ("Lat Pulldown", 3, 12, 0, "easy", "Controlled accessory."),
            ],
        ),
        (
            "Conditioning Reset",
            "2026-06-19",
            40,
            [
                ("Bike Intervals", 6, 0, 60, "hard", "Keep hard intervals crisp."),
                ("Kettlebell Swing", 4, 15, 0, "moderate", "Power conditioning."),
                ("Push Up", 3, 15, 0, "moderate", "Stop before form breaks."),
                ("Dead Bug", 3, 10, 0, "easy", "Recover breathing."),
                ("Incline Dumbbell Press", 3, 10, 0, "easy", "Light pump work."),
                ("Cable Row", 3, 12, 0, "easy", "Light pull work."),
            ],
        ),
    ]

    workouts = {}
    workout_exercises = {}
    for workout_name, date, expected_time, rows in workout_specs:
        workout, _ = Workout.objects.update_or_create(
            id=WORKOUT_IDS[workout_name],
            defaults={
                "user_id": str(user.id),
                "plan": plan,
                "name": workout_name,
                "date": date,
                "expected_time": expected_time,
            },
        )
        workouts[workout_name] = workout

        for exercise_name, sets, reps, time, effort, note in rows:
            workout_exercise, _ = WorkoutExercise.objects.update_or_create(
                id=WORKOUT_EXERCISE_IDS[(workout_name, exercise_name)],
                defaults={
                    "workout": workout,
                    "exercise": exercises[exercise_name],
                    "sets": sets,
                    "reps": reps,
                    "time": time,
                    "effort": effort,
                    "note": note,
                },
            )
            workout_exercises[(workout_name, exercise_name)] = workout_exercise

    recommendation, _ = Recommendation.objects.update_or_create(
        id=DEMO_RECOMMENDATION_ID,
        defaults={
            "user_id": str(user.id),
            "workout_id": workouts["Upper Body Strength"].id,
            "snapshot_version": workouts["Upper Body Strength"].updated_at.isoformat(),
            "status": "pending",
            "summary": "Reduce pressing volume and keep the session recovery-friendly.",
            "reason": "The athlete's recovery context suggests keeping intensity controlled while preserving the main movement pattern.",
        },
    )
    RecommendationOperation.objects.update_or_create(
        id=DEMO_OPERATION_ID,
        defaults={
            "recommendation": recommendation,
            "sequence": 1,
            "operation_type": "update_exercise",
            "payload_json": {
                "workout_exercise_id": str(workout_exercises[("Upper Body Strength", "Bench Press")].id),
                "changes": {"sets": 3, "reps": 6, "effort": "moderate"},
                "reason": "Lower the pressing volume while keeping the skill practice in place.",
            },
        },
    )


def remove_demo_training_plan(apps, schema_editor):
    User = apps.get_model("users", "User")
    Recommendation = apps.get_model("recommendation", "Recommendation")
    TrainingPlan = apps.get_model("training", "TrainingPlan")
    Workout = apps.get_model("training", "Workout")
    Exercise = apps.get_model("training", "Exercise")

    Recommendation.objects.filter(id=DEMO_RECOMMENDATION_ID).delete()
    Workout.objects.filter(id__in=WORKOUT_IDS.values()).delete()
    TrainingPlan.objects.filter(id=DEMO_PLAN_ID).delete()
    Exercise.objects.filter(id__in=EXERCISE_IDS.values()).delete()
    User.objects.filter(id=DEMO_USER_ID).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
        ("training", "0005_minimal_training_schema"),
        ("recommendation", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_demo_training_plan, remove_demo_training_plan),
    ]
