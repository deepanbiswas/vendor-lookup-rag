"""Tests for CSV ingestion."""

from pathlib import Path

import pytest
from qdrant_client import QdrantClient

from tests.fakes import FakeTextEmbedder, FakeVectorStore
from vendor_lookup_rag.config import Settings
from vendor_lookup_rag.ingestion import ingest_vendor_csv


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    p = tmp_path / "v.csv"
    p.write_text(
        "vendor_id,legal_name,city\n"
        "x1,TestCo,Munich\n",
        encoding="utf-8",
    )
    return p


def test_ingest_calls_embed_and_upsert(sample_csv: Path) -> None:
    emb = FakeTextEmbedder(vector=[0.0] * 768)
    store = FakeVectorStore()
    s = Settings(embedding_vector_size=768, qdrant_collection="c1")

    n = ingest_vendor_csv(
        sample_csv,
        settings=s,
        embedder=emb,
        store=store,
    )
    assert n == 1
    assert emb.calls
    assert store.ensure_collection_calls == 1
    assert len(store.upsert_batches) == 1
    assert len(store.upsert_batches[0]) == 1
    assert store.upsert_batches[0][0][0] == "x1"


def test_ingest_chunks_qdrant_upserts(tmp_path: Path) -> None:
    p = tmp_path / "many.csv"
    p.write_text(
        "vendor_id,legal_name,city\n"
        "a,Co A,Munich\n"
        "b,Co B,Berlin\n",
        encoding="utf-8",
    )
    emb = FakeTextEmbedder(vector=[0.0] * 768)
    store = FakeVectorStore()
    s = Settings(
        embedding_vector_size=768,
        qdrant_collection="c2",
        ingest_upsert_batch_size=1,
    )

    n = ingest_vendor_csv(p, settings=s, embedder=emb, store=store)
    assert n == 2
    assert len(store.upsert_batches) == 2


def test_ingest_rejects_empty_normalized_embedding_text(tmp_path: Path) -> None:
    p = tmp_path / "bad.csv"
    p.write_text(
        "vendor_id,legal_name\n"
        "x1,@@@\n",
        encoding="utf-8",
    )
    emb = FakeTextEmbedder()
    store = FakeVectorStore()
    s = Settings(embedding_vector_size=768, qdrant_collection="c3")
    with pytest.raises(ValueError, match=r"row 2.*vendor_id='x1'"):
        ingest_vendor_csv(p, settings=s, embedder=emb, store=store)
    assert emb.calls == []


def test_ingest_verbose_progress_stderr(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    p = tmp_path / "prog.csv"
    p.write_text(
        "vendor_id,legal_name\n"
        "a,A Co\n"
        "b,B Co\n",
        encoding="utf-8",
    )
    emb = FakeTextEmbedder(vector=[0.0] * 4)
    store = FakeVectorStore()
    s = Settings(
        embedding_vector_size=4,
        qdrant_collection="c4",
        ingest_upsert_batch_size=1,
    )
    ingest_vendor_csv(
        p,
        settings=s,
        embedder=emb,
        store=store,
        verbose=True,
        progress_every=1,
    )
    err = capsys.readouterr().err
    assert "Ingesting" in err
    assert "Ingest progress: 1 rows" in err
    assert "Ingest progress: 2 rows" in err


def test_ingest_progress_milestones_respect_batch_size(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Progress lines must fire at N, 2N, … even when upsert batch size does not divide N."""
    lines = ["vendor_id,legal_name\n"] + [f"id{i},Co {i}\n" for i in range(520)]
    p = tmp_path / "batches.csv"
    p.write_text("".join(lines), encoding="utf-8")
    emb = FakeTextEmbedder(vector=[0.0] * 8)
    store = FakeVectorStore()
    s = Settings(
        embedding_vector_size=8,
        qdrant_collection="milestone_c",
        ingest_upsert_batch_size=128,
    )
    ingest_vendor_csv(
        p,
        settings=s,
        embedder=emb,
        store=store,
        verbose=True,
        progress_every=500,
    )
    err = capsys.readouterr().err
    assert "Ingest progress: 500 rows indexed." in err


def test_ingest_streaming_counts_many_synthetic_rows(tmp_path: Path) -> None:
    """Streaming path: no full-file list in memory; batched upserts via port."""
    n_rows = 120
    lines = ["vendor_id,legal_name\n"] + [f"id{i},Company Number {i}\n" for i in range(n_rows)]
    p = tmp_path / "bulk.csv"
    p.write_text("".join(lines), encoding="utf-8")
    emb = FakeTextEmbedder(vector=[0.0] * 8)
    store = FakeVectorStore()
    s = Settings(
        embedding_vector_size=8,
        qdrant_collection="bulk_stream",
        ingest_upsert_batch_size=40,
    )
    count = ingest_vendor_csv(p, settings=s, embedder=emb, store=store)
    assert count == n_rows
    assert len(emb.calls) == n_rows
    assert len(store.upsert_batches) == 3
    assert sum(len(b) for b in store.upsert_batches) == n_rows


def test_ingest_without_store_uses_qdrant_client_path(sample_csv: Path) -> None:
    """Regression: omitting ``store`` still builds QdrantVectorStore from ``client``."""
    emb = FakeTextEmbedder(vector=[0.0] * 768)
    client = QdrantClient(":memory:")
    s = Settings(embedding_vector_size=768, qdrant_collection="regression_c")
    try:
        n = ingest_vendor_csv(sample_csv, settings=s, embedder=emb, client=client)
        assert n == 1
        assert len(emb.calls) == 1
    finally:
        client.close()
