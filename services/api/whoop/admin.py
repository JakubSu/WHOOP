from django.contrib import admin

from whoop.models import WhoopConnection, WhoopOAuthState, WhoopSnapshot


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
