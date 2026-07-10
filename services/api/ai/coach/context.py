from __future__ import annotations

from datetime import date
from typing import Any

from coaching.models import CoachConversation
from recommendation.models import Recommendation
from recommendation.services.workout_recommendation import (
    RecommendationNotFound,
    RecommendationValidationError,
    build_workout_recommendation_context,
)
from training import services as training_services
from training.models import TrainingPlan, Workout
from whoop.exceptions import WhoopConnectionNotFound, WhoopError
from whoop.workflows.summary import disconnected_summary


class CoachContextBuilder:
    def build(
        self,
        *,
        user_id: str,
        page_context: dict[str, Any],
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        page_type = str(page_context["page_type"])
        context_id = str(page_context.get("context_id") or "")
        shared = {
            "page_context": {
                "page_type": page_type,
                "context_id": context_id,
            },
            "conversation_history": self._conversation_history(conversation_id),
            "recommendations": self._recommendation_context(user_id),
        }
        if page_type == CoachConversation.PageType.WORKOUT:
            return {
                **shared,
                "whoop_summary": self._whoop_summary(user_id),
                "workout": build_workout_recommendation_context(
                    user_id,
                    context_id,
                ),
                "can_modify_workout": True,
            }
        if page_type == CoachConversation.PageType.TODAY_WORKOUT:
            landing = training_services.get_workout_landing(user_id, date.today())
            payload: dict[str, Any] = {
                **shared,
                "whoop_summary": self._whoop_summary(user_id),
                "today_workout": None,
                "can_modify_workout": False,
            }
            if landing is not None:
                payload["today_workout"] = self._workout_summary(landing.workout)
                payload["has_workout_today"] = landing.has_workout_today
                payload["can_modify_workout"] = landing.has_workout_today
                if landing.has_workout_today:
                    payload["workout"] = build_workout_recommendation_context(
                        user_id,
                        str(landing.workout.id),
                    )
            return payload
        if page_type == CoachConversation.PageType.TRAINING_PLAN:
            plan = training_services.get_training_plan(context_id, user_id)
            if plan is None:
                raise RecommendationNotFound("Training plan was not found.")
            workouts = training_services.list_plan_workouts(context_id, user_id)
            return {
                **shared,
                "whoop_summary": self._whoop_summary(user_id),
                "training_plan": self._plan_summary(plan),
                "workouts": [self._workout_summary(workout) for workout in workouts],
                "can_modify_workout": False,
            }
        if page_type == CoachConversation.PageType.RECOVERY:
            whoop_summary = self._whoop_summary(user_id)
            return {
                **shared,
                "whoop_summary": whoop_summary,
                "recent_workouts": whoop_summary.get("recent_workouts", []),
                "can_modify_workout": False,
            }
        raise RecommendationValidationError("Unsupported coach page type.")

    def _conversation_history(self, conversation_id: str | None) -> list[dict[str, Any]]:
        if not conversation_id:
            return []
        conversation = (
            CoachConversation.objects.filter(pk=conversation_id)
            .prefetch_related("messages")
            .first()
        )
        if conversation is None:
            return []
        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in conversation.messages.order_by("-created_at")[:8]
        ]

    def _recommendation_context(self, user_id: str) -> list[dict[str, Any]]:
        return [
            {
                "id": str(recommendation.id),
                "workout_id": str(recommendation.workout_id),
                "status": recommendation.status,
                "summary": recommendation.summary,
                "source": recommendation.source,
            }
            for recommendation in Recommendation.objects.filter(user_id=user_id)
            .order_by("-created_at")[:5]
        ]

    def _whoop_summary(self, user_id: str) -> dict[str, Any]:
        from whoop import services as whoop_services

        try:
            return whoop_services.create_summary_service().execute(user_id)
        except WhoopConnectionNotFound:
            return disconnected_summary()
        except WhoopError as exc:
            return {"connected": False, "detail": f"WHOOP summary unavailable: {exc}"}
        except Exception as exc:
            return {"connected": False, "detail": f"WHOOP summary unavailable: {exc}"}

    def _plan_summary(self, plan: TrainingPlan) -> dict[str, Any]:
        return {
            "id": str(plan.id),
            "name": plan.name,
            "start_date": plan.start_date.isoformat() if plan.start_date else None,
            "end_date": plan.end_date.isoformat() if plan.end_date else None,
        }

    def _workout_summary(self, workout: Workout) -> dict[str, Any]:
        return {
            "id": str(workout.id),
            "name": workout.name,
            "date": workout.date.isoformat() if workout.date else None,
            "expected_time": workout.expected_time,
        }
