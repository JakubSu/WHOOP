from django.contrib import admin

from training.models import Exercise, TrainingPlan, Workout, WorkoutExercise


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_favorite", "is_avoided", "updated_at")
    list_filter = ("category", "is_favorite", "is_avoided")
    search_fields = ("name", "primary_muscle_group", "equipment")


@admin.register(TrainingPlan)
class TrainingPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "goal", "status", "start_date", "end_date", "updated_at")
    list_filter = ("status",)
    search_fields = ("name", "goal", "notes")


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ("name", "workout_type", "status", "scheduled_date", "updated_at")
    list_filter = ("workout_type", "status")
    search_fields = ("name", "notes", "planned_intensity")


@admin.register(WorkoutExercise)
class WorkoutExerciseAdmin(admin.ModelAdmin):
    list_display = ("workout", "exercise", "position", "sets", "reps", "duration_seconds")
    list_filter = ("workout",)
    search_fields = ("workout__name", "exercise__name", "notes")
