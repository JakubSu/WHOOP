from pathlib import Path
from typing import Any, TypeVar

from django.test import SimpleTestCase
from pydantic import BaseModel

from ai.infrastructure.models import LoadedPrompt
from ai.infrastructure.llm_provider import LLMProvider
from ai.infrastructure.models import LLMRequestMetadata
from ai.recommendation.schemas import WorkoutPatchDraft
from ai.recommendation.services.workout_patch_generator import WorkoutPatchGenerator

ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


class FakePromptLoader:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def load(self, *, namespace: str, name: str, version: str) -> LoadedPrompt:
        self.calls.append({"namespace": namespace, "name": name, "version": version})
        return LoadedPrompt(
            namespace=namespace,
            name=name,
            version=version,
            template="Return a workout patch.",
            path=Path("fake.md"),
        )


class FakeProvider(LLMProvider):
    def __init__(self, response: WorkoutPatchDraft | dict[str, Any]) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def generate_structured(
        self,
        *,
        prompt: str,
        input_data: dict[str, Any],
        response_model: type[ResponseModelT],
        metadata: LLMRequestMetadata | None = None,
    ) -> ResponseModelT:
        self.calls.append(
            {
                "prompt": prompt,
                "input_data": input_data,
                "response_model": response_model,
                "metadata": metadata,
            }
        )
        if isinstance(self.response, WorkoutPatchDraft):
            if isinstance(self.response, response_model):
                return self.response
            return response_model.model_validate(
                self.response.model_dump(mode="json")
            )
        return response_model.model_validate(self.response)


class WorkoutPatchGeneratorTests(SimpleTestCase):
    def test_generator_loads_prompt_and_returns_typed_draft(self) -> None:
        draft = WorkoutPatchDraft.model_validate(
            {
                "summary": "Reduce fatigue.",
                "reason": "Recovery is low.",
                "operations": [
                    {
                        "op": "remove_exercise",
                        "workout_exercise_id": "workout-exercise-1",
                    }
                ],
            }
        )
        prompt_loader = FakePromptLoader()
        provider = FakeProvider(draft)

        result = WorkoutPatchGenerator(
            provider=provider,
            prompt_loader=prompt_loader,
        ).generate({"current_workout": {"id": "workout-1"}})

        self.assertIsInstance(result, WorkoutPatchDraft)
        self.assertEqual(result.summary, "Reduce fatigue.")
        self.assertEqual(prompt_loader.calls[0]["namespace"], "recommendation")
        self.assertEqual(prompt_loader.calls[0]["name"], "workout_patch_recommendation")
        self.assertEqual(prompt_loader.calls[0]["version"], "v1")
        self.assertEqual(provider.calls[0]["response_model"], WorkoutPatchDraft)
        self.assertEqual(provider.calls[0]["metadata"].prompt_version, "v1")

    def test_generator_validates_dict_response(self) -> None:
        provider = FakeProvider(
            {
                "summary": "Update workout.",
                "operations": [
                    {
                        "op": "update_exercise",
                        "workout_exercise_id": "workout-exercise-1",
                        "changes": {"sets": 3},
                    }
                ],
            }
        )

        result = WorkoutPatchGenerator(
            provider=provider,
            prompt_loader=FakePromptLoader(),
        ).generate({"current_workout": {"id": "workout-1"}})

        self.assertEqual(result.operations[0].op, "update_exercise")

    def test_generator_rejects_invalid_structured_output(self) -> None:
        provider = FakeProvider({"summary": "Invalid.", "operations": [{"op": "unknown"}]})

        with self.assertRaises(ValueError):
            WorkoutPatchGenerator(
                provider=provider,
                prompt_loader=FakePromptLoader(),
            ).generate({"current_workout": {"id": "workout-1"}})
