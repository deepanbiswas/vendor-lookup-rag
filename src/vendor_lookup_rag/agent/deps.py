"""Dependencies injected into the vendor lookup agent run."""

from __future__ import annotations

from dataclasses import dataclass

from vendor_lookup_rag.config import Settings
from vendor_lookup_rag.ports import TextEmbedder, VectorStore


@dataclass
class AgentDeps:
    """Dependencies injected into the agent run."""

    settings: Settings
    embedder: TextEmbedder
    store: VectorStore
