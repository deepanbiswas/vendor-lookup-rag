"""Tests for adapter factories."""

from __future__ import annotations

import pytest
from qdrant_client import QdrantClient

from vendor_lookup_rag.adapters.factory import (
    make_text_embedder,
    make_vendor_agent_runner,
    open_vector_store,
)
from vendor_lookup_rag.adapters.pydantic_ai import PydanticAiVendorAgent
from vendor_lookup_rag.adapters.qdrant import QdrantVectorStore
from vendor_lookup_rag.config import Settings
from vendor_lookup_rag.embedding import OllamaEmbedder


def test_open_vector_store_in_memory() -> None:
    s = Settings(embedding_vector_size=4, qdrant_collection="f")
    client = QdrantClient(":memory:")
    try:
        handle = open_vector_store(s, client=client)
        assert handle.own_client is False
        assert isinstance(handle.store, QdrantVectorStore)
        handle.store.ensure_collection()
    finally:
        client.close()


def test_open_vector_store_rejects_unknown_backend() -> None:
    s = Settings.model_construct(vector_backend="qdrant")  # type: ignore[arg-type]
    # model_construct bypasses validation; simulate bad value via cast for API test
    object.__setattr__(s, "vector_backend", "not_a_backend")  # type: ignore[misc]
    with pytest.raises(ValueError, match="Unsupported vector_backend"):
        open_vector_store(s)


def test_make_text_embedder_returns_ollama() -> None:
    s = Settings()
    emb = make_text_embedder(s)
    assert isinstance(emb, OllamaEmbedder)


def test_make_text_embedder_rejects_unknown_backend() -> None:
    s = Settings()
    object.__setattr__(s, "embedding_backend", "not_a_backend")  # type: ignore[misc]
    with pytest.raises(ValueError, match="Unsupported embedding_backend"):
        make_text_embedder(s)


def test_make_vendor_agent_runner_returns_pydantic_wrapper() -> None:
    s = Settings(agent_instrument=False)
    agent = make_vendor_agent_runner(s)
    assert isinstance(agent, PydanticAiVendorAgent)


def test_make_vendor_agent_runner_rejects_unknown_backend() -> None:
    s = Settings(agent_instrument=False)
    object.__setattr__(s, "agent_backend", "not_a_backend")  # type: ignore[misc]
    with pytest.raises(ValueError, match="Unsupported agent_backend"):
        make_vendor_agent_runner(s)
