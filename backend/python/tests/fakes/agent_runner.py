"""Fake :class:`~vendor_lookup_rag.ports.agent_runner.VendorAgentRunner` and run result shape."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FakeAgentUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass
class FakeAgentRunResult:
    """Mimics attributes read by :func:`vendor_lookup_rag.agent.run_trace.format_agent_run_trace`."""

    output: str
    run_id: str = "fake-run"
    usage_obj: FakeAgentUsage | None = None
    messages_json: bytes = field(default_factory=lambda: b"[]")

    def usage(self) -> FakeAgentUsage:
        return self.usage_obj if self.usage_obj is not None else FakeAgentUsage()

    def new_messages_json(self) -> bytes:
        return self.messages_json

    def _traceparent(self, required: bool = False) -> str | None:  # noqa: ARG002
        return None


class FakeVendorAgentRunner:
    def __init__(self, result: FakeAgentRunResult | None = None) -> None:
        self._result = result if result is not None else FakeAgentRunResult(output="ok")
        self.run_sync_calls: list[tuple[str, Any]] = []

    def run_sync(self, user_message: str, *, deps: Any) -> FakeAgentRunResult:
        self.run_sync_calls.append((user_message, deps))
        return self._result
