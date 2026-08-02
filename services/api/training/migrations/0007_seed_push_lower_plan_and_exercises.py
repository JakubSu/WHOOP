import uuid
from decimal import Decimal

from django.db import migrations

ATHLETE_USER_ID = uuid.UUID("a559a75b-8c55-4a41-a2c8-bd15b9c2d8a3")
PLAN_ID = uuid.UUID("a4e7c77b-aefa-4950-a584-7a10167723d6")

WORKOUT_IDS = {
    "Upper Push": uuid.UUID("be64131d-893e-4395-9852-a003e3609857"),
    "Lower Strength": uuid.UUID("49e122f1-5a51-4484-91db-fd360b982f74"),
}

WORKOUT_EXERCISE_IDS = {
    ("Upper Push", "Bench Press"): uuid.UUID("52cf4f73-d111-4064-9f72-fbc8e36269c1"),
    ("Upper Push", "Incline Bench Press"): uuid.UUID("a363579b-d083-4423-847e-54f7747cf492"),
    ("Upper Push", "Military Press"): uuid.UUID("a889f070-a03b-48ee-8f8f-0c6c876d7fdd"),
    ("Upper Push", "Push-Up"): uuid.UUID("d1cc5d2a-51b6-49df-bf0f-d75b439b2ef9"),
    ("Lower Strength", "Front Squat"): uuid.UUID("91099671-e623-47d6-9ff1-71409572f0a9"),
    ("Lower Strength", "Barbell Lunges"): uuid.UUID("93eeb043-fba2-4a7f-ab2a-abcf76fb7ad0"),
    ("Lower Strength", "Bulgarian Split Squat"): uuid.UUID("1693d37d-3068-4e32-a378-d48d59b7f266"),
    ("Lower Strength", "Goblet Squat"): uuid.UUID("3d421cd4-e8ea-4dd2-9be1-869d78e2ef6d"),
}

EXERCISE_DEFAULTS = [
    ("Bench Press", 4, 6, "Chest", "Compound upper-body press."),
    ("Incline Bench Press", 3, 8, "Chest", "Upper-chest barbell press."),
    ("Military Press", 3, 6, "Shoulders", "Strict standing overhead press."),
    ("Push-Up", 3, 15, "Chest", "Bodyweight press variation."),
    ("Dumbbell Bench Press", 3, 10, "Chest", "Dumbbell horizontal press."),
    ("Arnold Press", 3, 10, "Shoulders", "Rotating dumbbell shoulder press."),
    ("Close-Grip Bench Press", 3, 8, "Triceps", "Pressing variation with triceps emphasis."),
    ("Dips", 3, 10, "Triceps", "Bodyweight upper-body press."),
    ("Cable Chest Fly", 3, 12, "Chest", "Controlled chest isolation."),
    ("Dumbbell Lateral Raise", 3, 15, "Shoulders", "Side delt isolation."),
    ("Triceps Pushdown", 3, 12, "Triceps", "Cable triceps isolation."),
    ("Overhead Triceps Extension", 3, 12, "Triceps", "Long-head triceps isolation."),
    ("Skull Crusher", 3, 10, "Triceps", "Lying triceps extension."),
    ("Barbell Curl", 3, 10, "Biceps", "Loaded elbow flexion."),
    ("Dumbbell Curl", 3, 12, "Biceps", "Alternating biceps curl."),
    ("Hammer Curl", 3, 12, "Biceps", "Neutral-grip arm work."),
    ("Preacher Curl", 3, 10, "Biceps", "Supported biceps isolation."),
    ("Cable Curl", 3, 12, "Biceps", "Constant-tension biceps curl."),
    ("Reverse Curl", 3, 12, "Forearms", "Forearm and brachialis-focused curl."),
    ("Wrist Curl", 3, 15, "Forearms", "Forearm flexor isolation."),
    ("Back Squat", 4, 5, "Quads", "Compound lower-body lift."),
    ("Front Squat", 4, 5, "Quads", "Upright squat variation with quad emphasis."),
    ("Barbell Lunges", 3, 8, "Legs", "Loaded lunge variation."),
    ("Bulgarian Split Squat", 3, 10, "Legs", "Rear-foot elevated unilateral squat."),
    ("Goblet Squat", 3, 12, "Quads", "Dumbbell or kettlebell squat pattern."),
    ("Deadlift", 3, 5, "Posterior Chain", "Heavy full-body hinge."),
    ("Romanian Deadlift", 3, 8, "Hamstrings", "Hip hinge with hamstring emphasis."),
    ("Hip Thrust", 4, 8, "Glutes", "Loaded glute extension."),
    ("Leg Press", 4, 10, "Quads", "Machine lower-body press."),
    ("Leg Extension", 3, 12, "Quads", "Quad isolation movement."),
    ("Hamstring Curl", 3, 12, "Hamstrings", "Knee-flexion hamstring isolation."),
    ("Standing Calf Raise", 4, 12, "Calves", "Standing calf isolation."),
    ("Seated Calf Raise", 4, 15, "Calves", "Bent-knee calf isolation."),
    ("Step-Up", 3, 10, "Legs", "Single-leg step pattern."),
    ("Walking Lunge", 3, 12, "Legs", "Dynamic unilateral leg work."),
    ("Reverse Lunge", 3, 10, "Legs", "Backward lunge pattern."),
    ("Sumo Deadlift", 3, 5, "Posterior Chain", "Wide-stance deadlift variation."),
    ("Glute Bridge", 3, 12, "Glutes", "Floor-based hip extension."),
    ("Box Squat", 4, 5, "Quads", "Squat variation to a box target."),
    ("Hack Squat", 4, 10, "Quads", "Machine-supported squat pattern."),
]


def seed_push_lower_plan(apps, schema_editor):
    Exercise = apps.get_model("training", "Exercise")
    TrainingPlan = apps.get_model("training", "TrainingPlan")
    Workout = apps.get_model("training", "Workout")
    WorkoutExercise = apps.get_model("training", "WorkoutExercise")

    exercises = {}
    for name, default_sets, default_reps, muscle_group, notes in EXERCISE_DEFAULTS:
        exercise, _ = Exercise.objects.update_or_create(
            user_id="",
            name=name,
            defaults={
                "prescription_type": "strength",
                "default_sets": default_sets,
                "default_reps": default_reps,
                "muscle_group": muscle_group,
                "default_time": 0,
                "notes": notes,
            },
        )
        exercises[name] = exercise

    plan, _ = TrainingPlan.objects.update_or_create(
        id=PLAN_ID,
        defaults={
            "user_id": str(ATHLETE_USER_ID),
            "name": "Push and Lower Strength Block",
            "start_date": "2026-06-22",
            "end_date": "2026-06-28",
        },
    )

    workout_specs = [
        (
            "Upper Push",
            "2026-06-22",
            50,
            [
                ("Bench Press", 4, 6, Decimal("135.00"), "Primary horizontal press."),
                ("Incline Bench Press", 3, 8, Decimal("115.00"), "Upper-chest strength work."),
                ("Military Press", 3, 6, Decimal("95.00"), "Strict overhead pressing."),
                ("Push-Up", 3, 15, None, "Bodyweight finisher with clean reps."),
            ],
        ),
        (
            "Lower Strength",
            "2026-06-24",
            55,
            [
                ("Front Squat", 4, 5, Decimal("155.00"), "Main lower-body strength lift."),
                ("Barbell Lunges", 3, 8, Decimal("95.00"), "Count reps per side."),
                ("Bulgarian Split Squat", 3, 10, Decimal("35.00"), "Dumbbell load per hand."),
                ("Goblet Squat", 3, 12, Decimal("50.00"), "Controlled accessory squat."),
            ],
        ),
    ]

    for workout_name, date, expected_time, rows in workout_specs:
        workout, _ = Workout.objects.update_or_create(
            id=WORKOUT_IDS[workout_name],
            defaults={
                "user_id": str(ATHLETE_USER_ID),
                "plan": plan,
                "name": workout_name,
                "date": date,
                "expected_time": expected_time,
            },
        )

        for exercise_name, sets, reps, weight, note in rows:
            WorkoutExercise.objects.update_or_create(
                id=WORKOUT_EXERCISE_IDS[(workout_name, exercise_name)],
                defaults={
                    "workout": workout,
                    "exercise": exercises[exercise_name],
                    "sets": sets,
                    "reps": reps,
                    "time": 0,
                    "weight": weight,
                    "weight_unit": "lb",
                    "note": note,
                },
            )


def remove_push_lower_plan(apps, schema_editor):
    TrainingPlan = apps.get_model("training", "TrainingPlan")
    Workout = apps.get_model("training", "Workout")

    Workout.objects.filter(id__in=WORKOUT_IDS.values()).delete()
    TrainingPlan.objects.filter(id=PLAN_ID).delete()


class Migration(migrations.Migration):
    dependencies = [  # noqa: RUF012
        ("training", "0006_prescription_type_and_weight"),
    ]

    operations = [  # noqa: RUF012
        migrations.RunPython(seed_push_lower_plan, remove_push_lower_plan),
    ]
