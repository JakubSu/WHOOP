from django.urls import path

from coach.api.views import (
    ConversationCollectionAPIView,
    ConversationDetailAPIView,
    MessageCollectionAPIView,
    MessageStreamAPIView,
    UiActionDismissAPIView,
    UiActionResolveStreamAPIView,
)

urlpatterns = [
    path(
        "coach/conversations",
        ConversationCollectionAPIView.as_view(),
        name="coach-conversations",
    ),
    path(
        "coach/conversations/<uuid:conversation_id>",
        ConversationDetailAPIView.as_view(),
        name="coach-conversation-detail",
    ),
    path(
        "coach/conversations/<uuid:conversation_id>/messages",
        MessageCollectionAPIView.as_view(),
        name="coach-conversation-messages",
    ),
    path(
        "coach/conversations/<uuid:conversation_id>/messages/stream",
        MessageStreamAPIView.as_view(),
        name="coach-conversation-message-stream",
    ),
    path(
        "coach/conversations/<uuid:conversation_id>/ui-actions/<uuid:action_id>/resolve/stream",
        UiActionResolveStreamAPIView.as_view(),
        name="coach-ui-action-resolve-stream",
    ),
    path(
        "coach/conversations/<uuid:conversation_id>/ui-actions/<uuid:action_id>/dismiss",
        UiActionDismissAPIView.as_view(),
        name="coach-ui-action-dismiss",
    ),
]
