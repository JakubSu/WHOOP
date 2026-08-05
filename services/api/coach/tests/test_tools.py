from __future__ import annotations

import uuid
from typing import Any, cast

from django.contrib.auth import get_user_model
from django.test import TestCase

from coach.models import CoachConversation
from coach.tools import CoachToolContext, create_recommendation
from recommendation.contracts import RecommendationDraft
from recommendation.models import Recommendation, RecommendationOperation


class CoachToolTests(TestCase):
    """Verifies coach tools own recommendation creation before turn persistence."""

    def setUp(self) -> None:
        """Creates the user-owned conversation available to the coach tools."""

        user_model = get_user_model()
        self.user = cast(Any, user_model.objects).create_user(
            email="coach-tools@example.com",
            password="strong-password",
        )
        self.conversation = CoachConversation.objects.create(user=self.user)

    def test_create_recommendation_returns_an_existing_recommendation_id(self) -> None:
        """The write tool creates the ledger before the final coach result is saved."""

        recommendation_id = create_recommendation(
            CoachToolContext(user=self.user, conversation=self.conversation),
            draft=RecommendationDraft.model_validate(
                {
                    "summary": "Reduce volume",
                    "reason": "Recovery is lower than usual.",
                    "operations": [
                        {
                            "operation_type": "update_workout",
                            "reason": "Keep the session manageable.",
                            "payload": {
                                "workout_id": str(uuid.uuid4()),
                                "changes": {"name": "Easy session"},
                            },
                        }
                    ],
                }
            ),
        )

        recommendation = Recommendation.objects.get(pk=recommendation_id)
        operation = RecommendationOperation.objects.get(recommendation=recommendation)
        self.assertEqual(recommendation.conversation, self.conversation)
        self.assertIsNone(recommendation.coach_message)
        self.assertIsNone(operation.message)
