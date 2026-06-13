from pathlib import Path
from string import Formatter
from typing import Protocol

from django.conf import settings

from ai.infrastructure.exceptions import InvalidPromptReferenceError, PromptNotFoundError
from ai.infrastructure.models import LoadedPrompt


class PromptLoader(Protocol):
    def load(self, *, namespace: str, name: str, version: str) -> LoadedPrompt:
        ...


class FileSystemPromptLoader:
    def __init__(self, *, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or Path(settings.BASE_DIR) / "ai"

    def load(self, *, namespace: str, name: str, version: str) -> LoadedPrompt:
        self._validate_reference(namespace, name, version)
        path = self.base_dir / namespace / "prompts" / f"{name}.{version}.md"
        resolved_base = self.base_dir.resolve()
        resolved_path = path.resolve()
        if resolved_base not in resolved_path.parents:
            raise InvalidPromptReferenceError("Prompt path must stay inside the AI app.")
        if not resolved_path.exists():
            raise PromptNotFoundError(
                f"Prompt '{namespace}/{name}.{version}' was not found."
            )
        return LoadedPrompt(
            namespace=namespace,
            name=name,
            version=version,
            template=resolved_path.read_text(encoding="utf-8"),
            path=resolved_path,
        )

    def render(self, prompt: LoadedPrompt, values: dict[str, object]) -> str:
        formatter = Formatter()
        field_names = {
            field_name
            for _, field_name, _, _ in formatter.parse(prompt.template)
            if field_name
        }
        safe_values = {key: values.get(key, "") for key in field_names}
        return prompt.template.format(**safe_values)

    def _validate_reference(self, namespace: str, name: str, version: str) -> None:
        for value in (namespace, name, version):
            if not value or any(part in value for part in ("..", "/", "\\")):
                raise InvalidPromptReferenceError(
                    "Prompt namespace, name, and version must be simple path segments."
                )
