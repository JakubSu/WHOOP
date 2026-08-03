from django.urls import path

from coaching.api.views import (
    CoachActiveConversationAPIView,
    CoachConversationMessagesAPIView,
    CoachTurnStreamAPIView,
)

urlpatterns = [
    path(
        "coach/turns/stream/",
        CoachTurnStreamAPIView.as_view(),
        name="coach-turn-stream",
    ),
    path(
        "coach/conversations/active/",
        CoachActiveConversationAPIView.as_view(),
        name="coach-active-conversation",
    ),
    path(
        "coach/conversations/<uuid:conversation_id>/messages/",
        CoachConversationMessagesAPIView.as_view(),
        name="coach-conversation-messages",
    ),
]
