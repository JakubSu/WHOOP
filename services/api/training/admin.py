from django.contrib import admin

from training.models import Exercise, TrainingPlan, Workout, WorkoutExercise


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "prescription_type",
        "muscle_group",
        "default_sets",
        "default_reps",
        "default_time",
    )
    search_fields = ("name", "muscle_group", "notes")


@admin.register(TrainingPlan)
class TrainingPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date")
    search_fields = ("name",)


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ("name", "plan", "date", "expected_time")
    list_filter = ("plan",)
    search_fields = ("name",)


@admin.register(WorkoutExercise)
class WorkoutExerciseAdmin(admin.ModelAdmin):
    list_display = ("workout", "exercise", "sets", "reps", "time", "weight", "weight_unit")
    list_filter = ("workout",)
    search_fields = ("workout__name", "exercise__name", "note")
