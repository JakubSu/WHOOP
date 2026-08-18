from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "display_name", "whoop_user_id", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active")
    ordering = ("email",)
    search_fields = ("email", "display_name", "whoop_user_id")
    fieldsets = (
        (None, {"fields": ("email", "password")} ),
        ("Profile", {"fields": ("display_name", "whoop_user_id")} ),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")} ),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")} ),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")} ),
    )
    readonly_fields = ("created_at", "updated_at", "last_login")
