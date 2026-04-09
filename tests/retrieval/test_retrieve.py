"""Tests for retrieval."""

import json
from pathlib import Path

import pytest

from tests.fakes import FakeTextEmbedder, FakeVectorStore
from vendor_lookup_rag.config import Settings
from vendor_lookup_rag.models import SearchHit, VendorRecord
from vendor_lookup_rag.normalization import normalize_text
from vendor_lookup_rag.retrieval import retrieve_vendors


def test_retrieve_empty_query() -> None:
    emb = FakeTextEmbedder()
    store = FakeVectorStore()
    s = Settings()
    assert retrieve_vendors("   ", embedder=emb, store=store, settings=s) == []
    assert emb.calls == []


def test_retrieve_calls_embed_with_normalized_query() -> None:
    emb = FakeTextEmbedder(vector=[1.0, 0.0, 0.0])
    hit = SearchHit(score=0.9, record=VendorRecord(vendor_id="x", legal_name="Co"))
    store = FakeVectorStore(search_hits=[hit])
    s = Settings(retrieval_top_k=3)
    out = retrieve_vendors("Acme Berlin", embedder=emb, store=store, settings=s)
    assert len(emb.calls) == 1
    assert emb.calls[0] == normalize_text("Acme Berlin")
    assert len(store.search_calls) == 1
    assert store.search_calls[0][1] == 3
    assert out == [hit]


def test_retrieve_wraps_embed_failure() -> None:
    emb = FakeTextEmbedder(side_effect=ConnectionError("refused"))
    store = FakeVectorStore()
    s = Settings()
    with pytest.raises(RuntimeError, match="embedding"):
        retrieve_vendors("hello", embedder=emb, store=store, settings=s)
    assert store.search_calls == []


def test_retrieve_wraps_qdrant_failure() -> None:
    emb = FakeTextEmbedder(vector=[1.0, 0.0])
    store = FakeVectorStore(search_side_effect=RuntimeError("qdrant down"))
    s = Settings()
    with pytest.raises(RuntimeError, match="Qdrant"):
        retrieve_vendors("hello", embedder=emb, store=store, settings=s)


def test_retrieve_min_score_filters_hits() -> None:
    emb = FakeTextEmbedder(vector=[1.0, 0.0, 0.0])
    store = FakeVectorStore(
        search_hits=[
            SearchHit(score=0.4, record=VendorRecord(vendor_id="a", legal_name="Low")),
            SearchHit(score=0.95, record=VendorRecord(vendor_id="b", legal_name="High")),
        ],
    )
    s = Settings(retrieval_min_score=0.5)
    out = retrieve_vendors("q", embedder=emb, store=store, settings=s)
    assert len(out) == 1
    assert out[0].record.vendor_id == "b"


def test_retrieve_min_score_param_overrides_settings() -> None:
    emb = FakeTextEmbedder(vector=[1.0, 0.0, 0.0])
    store = FakeVectorStore(
        search_hits=[SearchHit(score=0.6, record=VendorRecord(vendor_id="a", legal_name="A"))],
    )
    s = Settings(retrieval_min_score=0.9)
    out = retrieve_vendors("q", embedder=emb, store=store, settings=s, min_score=0.5)
    assert len(out) == 1


def test_telemetry_writes_jsonl(tmp_path: Path) -> None:
    emb = FakeTextEmbedder(vector=[1.0, 0.0, 0.0])
    store = FakeVectorStore(search_hits=[])
    log_dir = tmp_path / "logs"
    s = Settings(
        telemetry_log_dir=str(log_dir),
        telemetry_log_to_stderr=False,
        retrieval_top_k=3,
    )
    retrieve_vendors("test query", embedder=emb, store=store, settings=s)
    log_file = log_dir / "vendor_retrieval.jsonl"
    assert log_file.is_file()
    line = log_file.read_text(encoding="utf-8").strip().splitlines()[-1]
    data = json.loads(line)
    assert data["event"] == "vendor_retrieval"
    assert "embed_ms" in data
    assert "search_ms" in data
    assert data["hit_count"] == 0
