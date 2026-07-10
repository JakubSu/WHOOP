from __future__ import annotations

import logging
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Protocol

from ai.coach.context import CoachContextBuilder
from ai.coach.safety import detect_safety_flags
from ai.coach.schemas import CoachTurnDraft
from ai.coach.ui_actions import AuthorizeUiActionService
from ai.infrastructure.llm_provider import LLMProvider
from ai.infrastructure.models import LLMRequestMetadata
from ai.infrastructure.prompt_loader import FileSystemPromptLoader, PromptLoader
from ai.infrastructure.services import get_llm_provider
from recommendation.models import Recommendation
from recommendation.services.workout_recommendation import (
    RecommendationValidationError,
    create_recommendation_from_workout_patch,
)


PROMPT_NAMESPACE = "coach"
PROMPT_NAME = "coach_turn"
PROMPT_VERSION = "v1"

logger = logging.getLogger(__name__)


class CoachTurnGeneratorProtocol(Protocol):
    def generate(self, context: dict[str, Any]) -> CoachTurnDraft: ...


class CoachTurnGenerator:
    def __init__(
        self,
        *,
        provider: LLMProvider | None = None,
        prompt_loader: PromptLoader | None = None,
    ) -> None:
        self.provider = provider
        self.prompt_loader = prompt_loader or FileSystemPromptLoader()

    def generate(self, context: dict[str, Any]) -> CoachTurnDraft:
        loaded_prompt = self.prompt_loader.load(
            namespace=PROMPT_NAMESPACE,
            name=PROMPT_NAME,
            version=PROMPT_VERSION,
        )
        logger.info(
            "coach_turn_llm_request_started prompt=%s.%s.%s context_keys=%s",
            PROMPT_NAMESPACE,
            PROMPT_NAME,
            PROMPT_VERSION,
            ",".join(sorted(context.keys())),
        )
        started_at = perf_counter()
        result = (self.provider or get_llm_provider()).generate_structured(
            prompt=loaded_prompt.template,
            input_data=context,
            response_model=CoachTurnDraft,
            metadata=LLMRequestMetadata(
                prompt_namespace=PROMPT_NAMESPACE,
                prompt_name=PROMPT_NAME,
                prompt_version=PROMPT_VERSION,
            ),
        )
        draft = result if isinstance(result, CoachTurnDraft) else CoachTurnDraft.model_validate(result)
        elapsed_ms = int((perf_counter() - started_at) * 1000)
        logger.info(
            "coach_turn_llm_request_completed prompt=%s.%s.%s elapsed_ms=%s progress_summaries=%s has_workout_patch=%s ui_actions=%s safety_flags=%s answer_length=%s",
            PROMPT_NAMESPACE,
            PROMPT_NAME,
            PROMPT_VERSION,
            elapsed_ms,
            len(draft.progress_summaries),
            draft.workout_patch is not None,
            len(draft.ui_actions),
            len(draft.safety_flags),
            len(draft.answer),
        )
        return draft


@dataclass
class CoachTurnResult:
    answer: str
    events: list[dict[str, Any]] = field(default_factory=list)
    recommendation: Recommendation | None = None
    ui_actions: list[dict[str, str]] = field(default_factory=list)
    safety_flags: list[str] = field(default_factory=list)


class CoachOrchestrator:
    def __init__(
        self,
        *,
        context_builder: CoachContextBuilder | None = None,
        generator: CoachTurnGeneratorProtocol | None = None,
        ui_action_service: AuthorizeUiActionService | None = None,
    ) -> None:
        self.context_builder = context_builder or CoachContextBuilder()
        self.generator = generator or CoachTurnGenerator()
        self.ui_action_service = ui_action_service or AuthorizeUiActionService()

    def run_turn(
        self,
        *,
        user_id: str,
        page_context: dict[str, Any],
        message: str,
        conversation_id: str | None = None,
    ) -> CoachTurnResult:
        started_at = perf_counter()
        logger.info(
            "coach_turn_orchestrator_started user_id=%s conversation_id=%s page_type=%s context_id=%s message_length=%s",
            user_id,
            conversation_id,
            page_context.get("page_type"),
            page_context.get("context_id"),
            len(message),
        )
        events: list[dict[str, Any]] = [
            {
                "event": "assistant_progress",
                "data": {"message": "I'll compare your page context and WHOOP summary."},
            }
        ]
        events.append(
            {
                "event": "tool_call_started",
                "data": {"tool": "build_coach_context", "label": "Reading coach context"},
            }
        )
        logger.info(
            "coach_turn_context_build_started user_id=%s conversation_id=%s page_type=%s context_id=%s",
            user_id,
            conversation_id,
            page_context.get("page_type"),
            page_context.get("context_id"),
        )
        context = self.context_builder.build(
            user_id=user_id,
            page_context=page_context,
            conversation_id=conversation_id,
        )
        logger.info(
            "coach_turn_context_build_completed user_id=%s conversation_id=%s context_keys=%s can_modify_workout=%s",
            user_id,
            conversation_id,
            ",".join(sorted(context.keys())),
            bool(context.get("can_modify_workout")),
        )
        events.append(
            {
                "event": "tool_call_completed",
                "data": {"tool": "build_coach_context", "summary": "Coach context ready."},
            }
        )
        context["user_message"] = message
        safety_flags = sorted(
            set(detect_safety_flags(message)) | set(context.get("safety_flags", []))
        )
        if safety_flags:
            context["safety_flags"] = safety_flags
        logger.info(
            "coach_turn_safety_checked user_id=%s conversation_id=%s safety_flags=%s",
            user_id,
            conversation_id,
            ",".join(safety_flags) if safety_flags else "none",
        )

        draft = self.generator.generate(context)
        for summary in draft.progress_summaries:
            events.append({"event": "assistant_progress", "data": {"message": summary}})

        safety_flags = sorted(set(safety_flags) | set(draft.safety_flags))
        proposed_ui_actions = [
            action.model_dump(mode="json") for action in draft.ui_actions
        ]
        ui_actions = self.ui_action_service.authorize(
            user_id=user_id,
            proposed_actions=proposed_ui_actions,
        )
        logger.info(
            "coach_turn_ui_actions_authorized user_id=%s conversation_id=%s proposed_actions=%s authorized_actions=%s",
            user_id,
            conversation_id,
            len(proposed_ui_actions),
            len(ui_actions),
        )
        for action in ui_actions:
            events.append({"event": "ui_action", "data": {"action": action}})

        recommendation = None
        if draft.workout_patch is not None:
            if not context.get("can_modify_workout"):
                raise RecommendationValidationError(
                    "Workout changes can only be proposed from workout context."
                )
            workout_id = self._workout_id_for_context(context)
            events.append(
                {
                    "event": "tool_call_started",
                    "data": {
                        "tool": "propose_workout_changes",
                        "label": "Creating workout proposal",
                    },
                }
            )
            logger.info(
                "coach_turn_recommendation_create_started user_id=%s conversation_id=%s workout_id=%s operations=%s",
                user_id,
                conversation_id,
                workout_id,
                len(draft.workout_patch.operations),
            )
            recommendation = create_recommendation_from_workout_patch(
                user_id=user_id,
                workout_id=workout_id,
                draft=draft.workout_patch,
                source=Recommendation.Source.COACH_CHAT,
                coach_conversation_id=conversation_id,
            )
            logger.info(
                "coach_turn_recommendation_created user_id=%s conversation_id=%s workout_id=%s recommendation_id=%s",
                user_id,
                conversation_id,
                workout_id,
                recommendation.id,
            )
            events.append(
                {
                    "event": "tool_call_completed",
                    "data": {
                        "tool": "propose_workout_changes",
                        "summary": "Workout proposal created for approval.",
                    },
                }
            )

        elapsed_ms = int((perf_counter() - started_at) * 1000)
        logger.info(
            "coach_turn_orchestrator_completed user_id=%s conversation_id=%s elapsed_ms=%s events=%s has_recommendation=%s safety_flags=%s ui_actions=%s",
            user_id,
            conversation_id,
            elapsed_ms,
            len(events),
            recommendation is not None,
            ",".join(safety_flags) if safety_flags else "none",
            len(ui_actions),
        )
        return CoachTurnResult(
            answer=draft.answer,
            events=events,
            recommendation=recommendation,
            ui_actions=ui_actions,
            safety_flags=safety_flags,
        )

    def _workout_id_for_context(self, context: dict[str, Any]) -> str:
        workout_context = context.get("workout")
        if isinstance(workout_context, dict):
            current_workout = workout_context.get("current_workout")
            if isinstance(current_workout, dict) and current_workout.get("id"):
                return str(current_workout["id"])
        page_context = context.get("page_context", {})
        return str(page_context.get("context_id"))
