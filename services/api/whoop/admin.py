from django.contrib import admin
from django.utils import timezone

from whoop.models import (
    WhoopAccessRequest,
    WhoopConnection,
    WhoopOAuthState,
    WhoopSnapshot,
)


@admin.register(WhoopAccessRequest)
class WhoopAccessRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "requested_at", "reviewed_at", "reviewed_by")
    list_filter = ("status", "requested_at", "reviewed_at")
    search_fields = ("user__email", "user__display_name")
    readonly_fields = ("id", "user", "requested_at")

    def save_model(self, request, obj, form, change):
        if obj.status in {
            WhoopAccessRequest.Status.APPROVED,
            WhoopAccessRequest.Status.REJECTED,
        }:
            if not obj.reviewed_at:
                obj.reviewed_at = timezone.now()
            if not obj.reviewed_by_id and request.user.is_authenticated:
                obj.reviewed_by = request.user
        else:
            obj.reviewed_at = None
            obj.reviewed_by = None
        super().save_model(request, obj, form, change)


@admin.register(WhoopConnection)
class WhoopConnectionAdmin(admin.ModelAdmin):
    list_display = ("user_id", "whoop_user_id", "expires_at", "connected_at", "revoked_at")
    list_filter = ("revoked_at", "connected_at")
    search_fields = ("user_id", "whoop_user_id")
    exclude = ("access_token_encrypted", "refresh_token_encrypted")
    readonly_fields = ("id", "connected_at", "created_at", "updated_at")


@admin.register(WhoopOAuthState)
class WhoopOAuthStateAdmin(admin.ModelAdmin):
    list_display = ("user_id", "expires_at", "consumed_at", "created_at")
    list_filter = ("consumed_at", "expires_at")
    search_fields = ("user_id",)
    exclude = ("state",)
    readonly_fields = ("id", "created_at")


@admin.register(WhoopSnapshot)
class WhoopSnapshotAdmin(admin.ModelAdmin):
    list_display = ("user_id", "snapshot_date", "recovery_score", "day_strain", "created_at")
    list_filter = ("snapshot_date",)
    search_fields = ("user_id",)
    readonly_fields = ("id", "created_at", "raw_payload")
