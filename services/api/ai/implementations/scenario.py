"""Deterministic development runner for exercising coach tools without an LLM."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from datetime import timedelta
from time import sleep
from typing import Any

from django.contrib.auth import get_user_model
from django.utils import timezone

from ai.runner import (
    ActivityChanged,
    CoachActivity,
    CoachRunner,
    CoachRunnerEvent,
    CoachRunRequest,
    CoachRunResult,
    RunCompleted,
    TextDelta,
)
from ai.tools import (
    CoachToolContext,
    create_recommendation,
    get_active_recommendation,
    get_whoop_summary,
    get_workout,
    search_exercises,
    search_workouts,
)
from coach.models import CoachConversation
from recommendation.contracts import RecommendationDraft

HELP_TEXT = "Supported test codes: /test search-workouts, /test recovery, /test propose-new-workout, /test modify-workout, /test replace-active, /test retry-create, /test fail-after-create"
INTER_TOOL_DELAY_SECONDS = 0.75
ActivitySink = Callable[[ActivityChanged], None]


class ScenarioRunnerError(RuntimeError):
    """Raised by the deliberate failure scenario after creating a recommendation."""


@dataclass(frozen=True)
class ScenarioContext:
    """The authenticated objects needed to run one deterministic scenario."""

    request: CoachRunRequest
    user: Any
    conversation: CoachConversation
    code: str

    def tool_context(self, step: str) -> CoachToolContext:
        return CoachToolContext(
            user=self.user,
            conversation=self.conversation,
            run_id=self.request.run_id,
            tool_call_id=f"scenario:{self.code}:{step}",
        )


class ScenarioCoachRunner:
    """Runs explicit message-code scenarios through the real coach tool interfaces."""

    async def run(self, request: CoachRunRequest) -> CoachRunResult:
        """Executes a scenario and returns its completed coach result."""

        return await asyncio.to_thread(self._execute, request)

    async def stream(self, request: CoachRunRequest) -> AsyncIterator[CoachRunnerEvent]:
        """Executes a scenario while exposing each tool call as progress activity."""

        events: asyncio.Queue[ActivityChanged | CoachRunResult | Exception] = (
            asyncio.Queue()
        )
        loop = asyncio.get_running_loop()

        def publish_activity(event: ActivityChanged) -> None:
            loop.call_soon_threadsafe(events.put_nowait, event)

        async def execute() -> None:
            try:
                result = await asyncio.to_thread(
                    self._execute,
                    request,
                    activity_events=publish_activity,
                )
                events.put_nowait(result)
            except Exception as exc:  # noqa: BLE001 - relay tool failures to the SSE consumer
                events.put_nowait(exc)

        execution = asyncio.create_task(execute())
        try:
            while True:
                item = await events.get()
                if isinstance(item, Exception):
                    raise item
                if isinstance(item, CoachRunResult):
                    yield TextDelta(item.content)
                    yield RunCompleted(item)
                    return
                yield item
        finally:
            execution.cancel()

    async def maintain_memory(self, *, conversation_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Deterministic scenario runs do not create model-backed memory."""

    def _execute(
        self,
        request: CoachRunRequest,
        *,
        activity_events: ActivitySink | None = None,
    ) -> CoachRunResult:
        scenario = self._scenario_context(request)
        handlers: dict[
            str, Callable[[ScenarioContext, ActivitySink | None], CoachRunResult]
        ] = {
            "/test search-workouts": self._search_workouts,
            "/test recovery": self._recovery,
            "/test propose-new-workout": self._propose_new_workout,
            "/test modify-workout": self._modify_workout,
            "/test replace-active": self._replace_active,
            "/test retry-create": self._retry_create,
            "/test fail-after-create": self._fail_after_create,
        }
        handler = handlers.get(scenario.code)
        if handler is None:
            return CoachRunResult(content=HELP_TEXT, ai_message_batch=[])

        # A brief pause before later tool calls makes the streaming activity UI
        # readable when the deterministic local tools complete immediately.
        emitted_tool_call = False

        def paced_activity_events(event: ActivityChanged) -> None:
            nonlocal emitted_tool_call
            if event.activity.status == "running":
                if emitted_tool_call:
                    sleep(INTER_TOOL_DELAY_SECONDS)
                emitted_tool_call = True
            if activity_events is not None:
                activity_events(event)

        return handler(
            scenario, paced_activity_events if activity_events is not None else None
        )

    def _scenario_context(self, request: CoachRunRequest) -> ScenarioContext:
        user_model = get_user_model()
        user = user_model.objects.filter(pk=request.user_id).first()
        conversation = CoachConversation.objects.filter(
            pk=request.conversation_id, user_id=request.user_id
        ).first()
        if user is None or conversation is None:
            raise ScenarioRunnerError(
                "Scenario request is outside the active conversation."
            )
        return ScenarioContext(
            request=request,
            user=user,
            conversation=conversation,
            code=request.content.strip(),
        )

    def _tool(
        self,
        scenario: ScenarioContext,
        events: ActivitySink | None,
        *,
        step: str,
        kind: str,
        label: str,
        call: Callable[[CoachToolContext], Any],
        tool_call_id: str | None = None,
    ) -> Any:
        resolved_tool_call_id = tool_call_id or step
        activity = CoachActivity(
            id=resolved_tool_call_id,
            kind=kind,  # type: ignore[arg-type]
            label=label,
            status="running",
        )
        if events is not None:
            events(ActivityChanged(activity))
        context = scenario.tool_context(resolved_tool_call_id)
        result = call(context)
        if events is not None:
            events(
                ActivityChanged(
                    CoachActivity(
                        id=activity.id,
                        kind=activity.kind,
                        label=activity.label,
                        status="completed",
                    )
                )
            )
        return result

    @staticmethod
    def _result(
        content: str, recommendation_id: uuid.UUID | None = None
    ) -> CoachRunResult:
        return CoachRunResult(
            content=content,
            ai_message_batch=[],
            recommendation_id=recommendation_id,
        )

    def _active_recommendation(
        self, scenario: ScenarioContext, events: ActivitySink | None
    ) -> Any:
        return self._tool(
            scenario,
            events,
            step="get-active",
            kind="recommendation",
            label="Loading the active recommendation",
            call=get_active_recommendation,
        )

    def _search_workouts(
        self, scenario: ScenarioContext, events: ActivitySink | None
    ) -> CoachRunResult:
        workouts = self._tool(
            scenario,
            events,
            step="search",
            kind="training_data",
            label="Searching workouts",
            call=search_workouts,
        )
        if not workouts:
            return self._result(
                "Setup needed: create a workout, then run /test search-workouts again."
            )
        workout = self._tool(
            scenario,
            events,
            step="get-workout",
            kind="training_data",
            label="Loading workout details",
            call=lambda context: get_workout(context, workout_id=workouts[0].id),
        )
        return self._result(
            f"Found {workout.name} on {workout.date} with {len(workout.exercises)} exercises."
        )

    def _recovery(
        self, scenario: ScenarioContext, events: ActivitySink | None
    ) -> CoachRunResult:
        summary = self._tool(
            scenario,
            events,
            step="get-summary",
            kind="recovery_data",
            label="Loading recovery data",
            call=get_whoop_summary,
        )
        if summary is None:
            return self._result(
                "WHOOP is not connected, so no recovery summary is available."
            )
        return self._result(f"Recovery summary: {summary.model_dump()}")

    def _propose_new_workout(
        self, scenario: ScenarioContext, events: ActivitySink | None
    ) -> CoachRunResult:
        exercises = self._tool(
            scenario,
            events,
            step="search-exercises",
            kind="training_data",
            label="Searching exercises",
            call=search_exercises,
        )
        if not exercises:
            return self._result(
                "Setup needed: add an exercise, then run /test propose-new-workout again."
            )
        exercise = exercises[0]
        temporary_workout_id = "workout_1"
        draft = RecommendationDraft.model_validate(
            {
                "summary": "Add a simple test workout",
                "operations": [
                    {
                        "operation_type": "add_exercise",
                        "reason": "Include an available exercise in the new workout.",
                        "payload": {
                            "workout": {
                                "kind": "new",
                                "temporary_id": temporary_workout_id,
                            },
                            "exercise_id": str(exercise.id),
                            "prescription": {"type": "reps", "sets": 3, "reps": 10},
                            "position": 0,
                        },
                    },
                    {
                        "operation_type": "add_workout",
                        "reason": "Create the parent workout.",
                        "payload": {
                            "temporary_id": temporary_workout_id,
                            "name": "Scenario test workout",
                            "date": (
                                timezone.localdate() + timedelta(days=1)
                            ).isoformat(),
                            "expected_time": 30,
                        },
                    },
                ],
            }
        )
        created = self._create(
            scenario,
            events,
            draft=draft,
        )
        return self._result(
            "Created a new-workout recommendation.", created.recommendation_id
        )

    def _modify_workout(
        self, scenario: ScenarioContext, events: ActivitySink | None
    ) -> CoachRunResult:
        workouts = self._tool(
            scenario,
            events,
            step="search",
            kind="training_data",
            label="Searching workouts",
            call=search_workouts,
        )
        if not workouts:
            return self._result(
                "Setup needed: create a workout, then run /test modify-workout again."
            )
        workout = self._tool(
            scenario,
            events,
            step="get-workout",
            kind="training_data",
            label="Loading workout details",
            call=lambda context: get_workout(context, workout_id=workouts[0].id),
        )
        draft = RecommendationDraft.model_validate(
            {
                "summary": f"Adjust {workout.name}",
                "operations": [
                    {
                        "operation_type": "update_workout",
                        "reason": "Make a small, visible duration adjustment.",
                        "payload": {
                            "workout_id": str(workout.id),
                            "changes": {"expected_time": workout.expected_time + 5},
                        },
                    }
                ],
            }
        )
        created = self._create(
            scenario,
            events,
            draft=draft,
        )
        return self._result(
            f"Created an update recommendation for {workout.name}.",
            created.recommendation_id,
        )

    def _replace_active(
        self, scenario: ScenarioContext, events: ActivitySink | None
    ) -> CoachRunResult:
        active = self._active_recommendation(scenario, events)
        if active is None:
            return self._result(
                "Setup needed: create an active recommendation before running /test replace-active."
            )
        workouts = self._tool(
            scenario,
            events,
            step="search",
            kind="training_data",
            label="Searching workouts",
            call=search_workouts,
        )
        targeted_workout_ids = {
            str(operation.payload.workout_id)
            for operation in active.draft.operations
            if getattr(operation.payload, "workout_id", None) is not None
        }
        replacement_summary = next(
            (
                workout
                for workout in workouts
                if str(workout.id) not in targeted_workout_ids
            ),
            None,
        )
        if replacement_summary is None:
            return self._result(
                "Setup needed: create a workout not targeted by the active recommendation before running /test replace-active."
            )
        workout = self._tool(
            scenario,
            events,
            step="get-workout",
            kind="training_data",
            label="Loading replacement workout details",
            call=lambda context: get_workout(
                context, workout_id=replacement_summary.id
            ),
        )
        draft = RecommendationDraft.model_validate(
            {
                "summary": f"Replace the proposal with an update to {workout.name}",
                "operations": [
                    {
                        "operation_type": "update_workout",
                        "reason": "Target a different workout than the active proposal.",
                        "payload": {
                            "workout_id": str(workout.id),
                            "changes": {"expected_time": workout.expected_time + 10},
                        },
                    }
                ],
            }
        )
        created = self._create(scenario, events, draft=draft)
        return self._result(
            "Replaced the active recommendation.", created.recommendation_id
        )

    def _retry_create(
        self, scenario: ScenarioContext, events: ActivitySink | None
    ) -> CoachRunResult:
        workouts = self._tool(
            scenario,
            events,
            step="search",
            kind="training_data",
            label="Searching workouts",
            call=search_workouts,
        )
        if not workouts:
            return self._result(
                "Setup needed: create a workout, then run /test retry-create again."
            )
        workout = self._tool(
            scenario,
            events,
            step="get-workout",
            kind="training_data",
            label="Loading workout details",
            call=lambda context: get_workout(context, workout_id=workouts[0].id),
        )
        draft = RecommendationDraft.model_validate(
            {
                "summary": f"Retry test for {workout.name}",
                "operations": [
                    {
                        "operation_type": "update_workout",
                        "reason": "Make a retry-safe duration adjustment.",
                        "payload": {
                            "workout_id": str(workout.id),
                            "changes": {"expected_time": workout.expected_time + 1},
                        },
                    }
                ],
            }
        )
        first = self._create(
            scenario,
            events,
            draft=draft,
            step="create-first",
            tool_call_id="create",
        )
        second = self._create(
            scenario,
            events,
            draft=draft,
            step="create-retry",
            tool_call_id="create",
        )
        if first.recommendation_id != second.recommendation_id:
            raise ScenarioRunnerError(
                "Scenario retry created more than one recommendation."
            )
        return self._result(
            "Retry returned the original recommendation.", first.recommendation_id
        )

    def _fail_after_create(
        self, scenario: ScenarioContext, events: ActivitySink | None
    ) -> CoachRunResult:
        exercises = self._tool(
            scenario,
            events,
            step="search-exercises",
            kind="training_data",
            label="Searching exercises",
            call=search_exercises,
        )
        if not exercises:
            return self._result(
                "Setup needed: add an exercise, then run /test fail-after-create again."
            )
        if self._active_recommendation(scenario, events) is not None:
            return self._result(
                "Setup needed: use a conversation without an active recommendation for /test fail-after-create."
            )
        exercise = exercises[0]
        temporary_workout_id = "workout_1"
        draft = RecommendationDraft.model_validate(
            {
                "summary": "Failed-run cleanup test",
                "operations": [
                    {
                        "operation_type": "add_workout",
                        "reason": "Create a proposal that will be expired.",
                        "payload": {
                            "temporary_id": temporary_workout_id,
                            "name": f"Failed scenario {exercise.name}",
                            "date": (
                                timezone.localdate() + timedelta(days=1)
                            ).isoformat(),
                            "expected_time": 20,
                        },
                    }
                ],
            }
        )
        self._create(scenario, events, draft=draft)
        raise ScenarioRunnerError("Deliberate failure after recommendation creation.")

    def _create(
        self,
        scenario: ScenarioContext,
        events: ActivitySink | None,
        *,
        draft: RecommendationDraft,
        step: str = "create",
        tool_call_id: str | None = None,
    ) -> Any:
        return self._tool(
            scenario,
            events,
            step=step,
            kind="recommendation",
            label="Creating recommendation",
            tool_call_id=tool_call_id,
            call=lambda context: create_recommendation(
                context,
                draft=draft,
            ),
        )


def create_scenario_runner() -> CoachRunner:
    """Creates the opt-in deterministic development runner."""

    return ScenarioCoachRunner()
