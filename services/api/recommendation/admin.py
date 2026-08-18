from django.contrib import admin

from recommendation.models import Recommendation, RecommendationOperation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("summary", "user", "source", "status", "created_at", "updated_at")
    list_filter = ("source", "status", "created_at")
    search_fields = ("summary", "user__email", "run_id", "tool_call_id")
    readonly_fields = ("id", "created_at", "updated_at", "expired_at", "superseded_at")
    list_select_related = ("user", "conversation", "coach_message", "replaced_by")


@admin.register(RecommendationOperation)
class RecommendationOperationAdmin(admin.ModelAdmin):
    list_display = ("recommendation", "operation_type", "status", "created_at", "resolved_at")
    list_filter = ("operation_type", "status", "created_at")
    search_fields = ("recommendation__user__email", "display_text", "reason")
    readonly_fields = ("id", "created_at", "updated_at", "resolved_at")
    list_select_related = ("recommendation", "recommendation__user")
