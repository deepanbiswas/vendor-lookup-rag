"""Agent orchestration port (framework-agnostic surface)."""

from __future__ import annotations

from typing import Any, Protocol, TypeVar

DepsT = TypeVar("DepsT")


class VendorAgentRunner(Protocol[DepsT]):
    """Runs a chat turn with injected dependencies (e.g. retrieval tools)."""

    def run_sync(self, user_message: str, *, deps: DepsT) -> Any:
        """Execute one synchronous agent turn; result shape is adapter-specific."""
        ...
