from typing import Any

from pydantic import BaseModel, ConfigDict

from ai.recommendation.schemas import WorkoutPatchDraft


def remove_json_schema_defaults(schema: dict[str, Any]) -> None:
    schema.pop("default", None)
    for value in schema.values():
        if isinstance(value, dict):
            remove_json_schema_defaults(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    remove_json_schema_defaults(item)


class CoachUiActionDraft(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra=remove_json_schema_defaults,
    )

    type: str
    target: str
    id: str


class CoachTurnDraft(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra=remove_json_schema_defaults,
    )

    answer: str
    progress_summaries: list[str] = []
    workout_patch: WorkoutPatchDraft | None = None
    ui_actions: list[CoachUiActionDraft] = []
    safety_flags: list[str] = []
