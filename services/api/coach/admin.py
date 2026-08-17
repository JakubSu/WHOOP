from django.contrib import admin

from coach.models import CoachConversation, CoachMessage, UiAction


class CoachMessageInline(admin.TabularInline):
    model = CoachMessage
    extra = 0
    fields = ("role", "content", "created_at")
    readonly_fields = ("role", "content", "created_at")
    show_change_link = True
    can_delete = False
    ordering = ("created_at",)


@admin.register(CoachConversation)
class CoachConversationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "updated_at", "created_at")
    list_select_related = ("user",)
    search_fields = ("title", "user__email")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = (CoachMessageInline,)


@admin.register(CoachMessage)
class CoachMessageAdmin(admin.ModelAdmin):
    list_display = ("role", "conversation", "user", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("content", "conversation__title", "conversation__user__email")
    readonly_fields = ("id", "created_at")
    list_select_related = ("conversation", "conversation__user")

    @admin.display(ordering="conversation__user__email", description="User")
    def user(self, obj: CoachMessage) -> str:
        return obj.conversation.user.email


@admin.register(UiAction)
class UiActionAdmin(admin.ModelAdmin):
    list_display = ("type", "status", "message", "created_at", "resolved_at")
    list_filter = ("status", "type")
    search_fields = ("type", "message__conversation__user__email")
    readonly_fields = ("id", "created_at", "resolved_at")
    list_select_related = (
        "message",
        "message__conversation",
        "message__conversation__user",
    )
