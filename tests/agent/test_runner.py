"""Tests for vendor agent wiring and search_vendors tool body."""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
from qdrant_client import QdrantClient

from vendor_lookup_rag.agent import (
    AgentDeps,
    build_vendor_agent,
    runner as agent_mod,
    search_vendors_tool_body,
)
from vendor_lookup_rag.config import Settings
from vendor_lookup_rag.adapters.ollama import OllamaEmbedder
from vendor_lookup_rag.adapters.qdrant import QdrantVectorStore
from vendor_lookup_rag.matching import MatchKind, MatchResult
from vendor_lookup_rag.models import SearchHit, SearchVendorToolError, SearchVendorToolSuccess, VendorRecord


def _minimal_deps() -> AgentDeps:
    s = Settings(agent_instrument=False)
    client = QdrantClient(":memory:")
    store = QdrantVectorStore(client, "t", s.embedding_vector_size)
    emb = OllamaEmbedder(s.ollama_base_url, s.embedding_model)
    return AgentDeps(settings=s, embedder=emb, store=store)


def test_build_vendor_agent_registers_search_vendors_tool() -> None:
    s = Settings(agent_instrument=False)
    agent = build_vendor_agent(s)
    inner = agent.pydantic_agent
    assert "search_vendors" in inner._function_toolset.tools
    assert inner.instrument is False


def test_build_vendor_agent_respects_agent_instrument_true() -> None:
    s = Settings(agent_instrument=True)
    agent = build_vendor_agent(s)
    assert agent.pydantic_agent.instrument is True


def test_search_vendors_tool_body_success_shape() -> None:
    deps = _minimal_deps()
    r = VendorRecord(
        vendor_id="v1",
        legal_name="Acme Corp",
        city="Berlin",
    )
    hit = SearchHit(score=0.95, record=r)
    match = MatchResult(
        kind=MatchKind.EXACT,
        hits=[hit],
        message="ok",
    )
    try:
        with (
            patch.object(agent_mod, "retrieve_vendors", return_value=[hit]),
            patch.object(agent_mod, "classify_matches", return_value=match),
        ):
            out = search_vendors_tool_body(deps, "Acme Berlin")
        assert isinstance(out, SearchVendorToolSuccess)
        assert out.ok is True
        assert out.kind == "exact"
        assert len(out.candidates) == 1
        assert len(out.retrieval_top_k) == 1
        assert out.candidates[0].vendor_id == "v1"
        assert out.candidates[0].score == 0.95
    finally:
        deps.embedder.close()


def test_search_vendors_tool_body_retrieval_top_k_includes_all_retrieved_hits() -> None:
    """``retrieval_top_k`` mirrors raw vector hits; ``candidates`` follow classify output."""
    deps = _minimal_deps()
    r1 = VendorRecord(vendor_id="a", legal_name="High", city="C1")
    r2 = VendorRecord(vendor_id="b", legal_name="Low", city="C2")
    r3 = VendorRecord(vendor_id="c", legal_name="Low2", city="C3")
    h1 = SearchHit(score=0.95, record=r1)
    h2 = SearchHit(score=0.50, record=r2)
    h3 = SearchHit(score=0.49, record=r3)
    match = MatchResult(kind=MatchKind.EXACT, hits=[h1], message="ok")
    try:
        with (
            patch.object(agent_mod, "retrieve_vendors", return_value=[h1, h2, h3]),
            patch.object(agent_mod, "classify_matches", return_value=match),
        ):
            out = search_vendors_tool_body(deps, "query")
        assert isinstance(out, SearchVendorToolSuccess)
        assert len(out.retrieval_top_k) == 3
        assert len(out.candidates) == 1
        assert out.candidates[0].vendor_id == "a"
    finally:
        deps.embedder.close()


def test_search_vendors_tool_passes_score_tolerance_to_classify() -> None:
    """Regression: runner forwards ``Settings.score_tolerance`` into ``classify_matches``."""
    s = Settings(agent_instrument=False, score_tolerance=0.12)
    client = QdrantClient(":memory:")
    store = QdrantVectorStore(client, "t", s.embedding_vector_size)
    emb = OllamaEmbedder(s.ollama_base_url, s.embedding_model)
    deps = AgentDeps(settings=s, embedder=emb, store=store)
    captured: dict = {}

    def fake_classify(**kwargs: object) -> MatchResult:
        captured.update(kwargs)
        return MatchResult(kind=MatchKind.NONE, hits=[], message="none")

    try:
        with (
            patch.object(agent_mod, "retrieve_vendors", return_value=[]),
            patch.object(agent_mod, "classify_matches", side_effect=fake_classify),
        ):
            search_vendors_tool_body(deps, "query text")
        assert captured.get("score_tolerance") == 0.12
        assert captured.get("score_exact") == s.score_threshold_exact
        assert captured.get("score_partial") == s.score_threshold_partial
    finally:
        deps.embedder.close()
        client.close()


def test_search_vendors_tool_body_runtime_error() -> None:
    deps = _minimal_deps()
    try:
        with patch.object(
            agent_mod,
            "retrieve_vendors",
            side_effect=RuntimeError("Failed to compute embedding"),
        ):
            out = search_vendors_tool_body(deps, "x")
        assert isinstance(out, SearchVendorToolError)
        assert out.ok is False
        assert out.error == "retrieval_failed"
        assert "embedding" in out.message
    finally:
        deps.embedder.close()


def test_import_streamlit_app() -> None:
    import vendor_lookup_rag.app  # noqa: F401


@pytest.mark.requires_ollama
def test_agent_run_sync_when_ollama_available() -> None:
    """Optional: real Ollama + chat model; skipped if server or model missing."""
    s = Settings(agent_instrument=False)
    try:
        r = httpx.get(f"{s.ollama_base_url}/api/tags", timeout=3.0)
        r.raise_for_status()
    except Exception:
        pytest.skip("Ollama not reachable")
    data = r.json()
    names = {m.get("name", "") for m in data.get("models", [])}
    if s.chat_model not in names and not any(
        s.chat_model in n for n in names
    ):
        pytest.skip(f"Chat model {s.chat_model!r} not pulled in Ollama")

    deps = _minimal_deps()
    try:
        agent = build_vendor_agent(s)
        result = agent.run_sync("Say only the word: ok", deps=deps)
        assert isinstance(result.output, str)
        assert len(result.output) > 0
    finally:
        deps.embedder.close()
