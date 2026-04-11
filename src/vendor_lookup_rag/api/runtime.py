"""Application runtime: agent, deps, and settings (REST API process)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from vendor_lookup_rag.agent.deps import AgentDeps
from vendor_lookup_rag.config import Settings

if TYPE_CHECKING:
    from vendor_lookup_rag.adapters.factory import VectorStoreHandle


@dataclass
class AppRuntime:
    """Holds injected dependencies for one API process lifetime."""

    agent: Any
    deps: AgentDeps
    settings: Settings
    vector_handle: VectorStoreHandle | None = None

    def shutdown(self) -> None:
        """Close embedding HTTP client and optionally Qdrant client when owned."""
        emb = self.deps.embedder
        close_fn = getattr(emb, "close", None)
        if callable(close_fn):
            close_fn()
        if self.vector_handle is not None and self.vector_handle.own_client:
            self.vector_handle.qdrant_client.close()
