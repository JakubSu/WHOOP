from ai.infrastructure.llm_provider import LLMProvider
from ai.infrastructure.models import LLMRequestMetadata
from ai.infrastructure.prompt_loader import FileSystemPromptLoader, PromptLoader
from ai.infrastructure.services import get_llm_provider
from ai.recommendation.schemas import WorkoutPatchDraft

PROMPT_NAMESPACE = "recommendation"
PROMPT_NAME = "workout_patch_recommendation"
PROMPT_VERSION = "v1"


class WorkoutPatchGenerator:
    def __init__(
        self,
        *,
        provider: LLMProvider | None = None,
        prompt_loader: PromptLoader | None = None,
    ) -> None:
        self.provider = provider
        self.prompt_loader = prompt_loader or FileSystemPromptLoader()

    def generate(self, context: dict[str, object]) -> WorkoutPatchDraft:
        loaded_prompt = self.prompt_loader.load(
            namespace=PROMPT_NAMESPACE,
            name=PROMPT_NAME,
            version=PROMPT_VERSION,
        )
        result = (self.provider or get_llm_provider()).generate_structured(
            prompt=loaded_prompt.template,
            input_data=context,
            response_model=WorkoutPatchDraft,
            metadata=LLMRequestMetadata(
                prompt_namespace=PROMPT_NAMESPACE,
                prompt_name=PROMPT_NAME,
                prompt_version=PROMPT_VERSION,
            ),
        )
        if isinstance(result, WorkoutPatchDraft):
            return result
        return WorkoutPatchDraft.model_validate(result)
