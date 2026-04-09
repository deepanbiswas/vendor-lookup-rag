"""Factories for concrete adapters, selected by :class:`~vendor_lookup_rag.config.settings.Settings`.

Add new ``Literal`` values on settings and branch here when introducing alternate backends.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from qdrant_client import QdrantClient

_logger = logging.getLogger(__name__)

from vendor_lookup_rag.adapters.ollama import OllamaEmbedder
from vendor_lookup_rag.adapters.qdrant import QdrantVectorStore
from vendor_lookup_rag.config import Settings, get_settings
from vendor_lookup_rag.ports import TextEmbedder, VectorStore

if TYPE_CHECKING:
    from vendor_lookup_rag.adapters.pydantic_ai import PydanticAiVendorAgent


@dataclass(frozen=True)
class VectorStoreHandle:
    """Vector store plus Qdrant client handle for lifecycle (``close``) when this code owns the client."""

    store: VectorStore
    qdrant_client: QdrantClient
    own_client: bool


def open_vector_store(
    settings: Settings | None = None,
    *,
    client: QdrantClient | None = None,
    check_compatibility: bool = True,
) -> VectorStoreHandle:
    """
    Build the vector index adapter implied by ``settings.vector_backend``.

    For Qdrant, returns a store wrapping ``client`` or a new :class:`~qdrant_client.QdrantClient`.
    """
    s = settings or get_settings()
    if s.vector_backend != "qdrant":
        _logger.error("Unsupported vector_backend: %s", s.vector_backend)
        raise ValueError(
            f"Unsupported vector_backend {s.vector_backend!r}. "
            "Add a branch in vendor_lookup_rag.adapters.factory.open_vector_store."
        )
    own_client = client is None
    qc = client or QdrantClient(url=s.qdrant_url, check_compatibility=check_compatibility)
    store = QdrantVectorStore(qc, s.qdrant_collection, s.embedding_vector_size)
    _logger.info(
        "Opened vector store backend=%s collection=%s own_client=%s",
        s.vector_backend,
        s.qdrant_collection,
        own_client,
    )
    return VectorStoreHandle(store=store, qdrant_client=qc, own_client=own_client)


def make_text_embedder(settings: Settings | None = None) -> TextEmbedder:
    """Build the :class:`~vendor_lookup_rag.ports.embedding.TextEmbedder` for ``settings.embedding_backend``."""
    s = settings or get_settings()
    if s.embedding_backend != "ollama":
        _logger.error("Unsupported embedding_backend: %s", s.embedding_backend)
        raise ValueError(
            f"Unsupported embedding_backend {s.embedding_backend!r}. "
            "Add a branch in vendor_lookup_rag.adapters.factory.make_text_embedder."
        )
    _logger.info(
        "Created text embedder backend=%s model=%s",
        s.embedding_backend,
        s.embedding_model,
    )
    return OllamaEmbedder(s.ollama_base_url, s.embedding_model)


def make_vendor_agent_runner(settings: Settings | None = None) -> PydanticAiVendorAgent:
    """Build the :class:`~vendor_lookup_rag.ports.agent_runner.VendorAgentRunner` for ``settings.agent_backend``."""
    s = settings or get_settings()
    if s.agent_backend != "pydantic_ai":
        _logger.error("Unsupported agent_backend: %s", s.agent_backend)
        raise ValueError(
            f"Unsupported agent_backend {s.agent_backend!r}. "
            "Add a branch in vendor_lookup_rag.adapters.factory.make_vendor_agent_runner."
        )
    # Local import avoids circular import (factory → pydantic_ai → agent → pydantic_ai).
    from vendor_lookup_rag.adapters.pydantic_ai import build_vendor_agent

    _logger.info("Creating agent runner backend=%s chat_model=%s", s.agent_backend, s.chat_model)
    return build_vendor_agent(s)
