"""Deterministic runner doubles used by Coach API tests."""

from collections.abc import Iterable
from time import sleep

from ai.runner import CoachRunnerEvent, CoachRunRequest, CoachRunResult


class ScriptedRunner:
    """A configurable runner double used to exercise Coach API paths."""

    result = CoachRunResult(content="Ready.", ai_message_batch=[])
    events: list[CoachRunnerEvent] = []
    requests: list[CoachRunRequest] = []
    stream_delay = 0.0

    def run(self, request: CoachRunRequest) -> CoachRunResult:
        """Records the request and returns the configured non-streaming result."""

        self.requests.append(request)
        return self.result

    def stream(self, request: CoachRunRequest) -> Iterable[CoachRunnerEvent]:
        """Records the request and yields configured events after an optional delay."""

        self.requests.append(request)
        if self.stream_delay:
            sleep(self.stream_delay)
        yield from self.events


runner = ScriptedRunner()


def create_runner() -> ScriptedRunner:
    """Returns the shared scripted runner configured by individual tests."""

    return runner
