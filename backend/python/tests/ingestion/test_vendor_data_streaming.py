"""Optional slow tests against ``data/vendor-data.csv`` (streaming iterator + ingest).

Run explicitly: ``pytest -m large_csv`` (excluded from default ``pytest`` via addopts).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.fakes import FakeTextEmbedder, FakeVectorStore
from vendor_lookup_rag.config import Settings
from vendor_lookup_rag.csv import iter_vendor_csv
from vendor_lookup_rag.ingestion import ingest_vendor_csv

VENDOR_DATA_CSV = Path(__file__).resolve().parents[2] / "data" / "vendor-data.csv"


@pytest.mark.large_csv
def test_vendor_data_csv_line_count_matches_iter_streaming() -> None:
    if not VENDOR_DATA_CSV.is_file():
        pytest.skip(f"Missing {VENDOR_DATA_CSV}")
    with VENDOR_DATA_CSV.open(encoding="utf-8") as f:
        expected = max(0, sum(1 for _ in f) - 1)
    n = sum(1 for _ in iter_vendor_csv(VENDOR_DATA_CSV))
    assert n == expected


@pytest.mark.large_csv
def test_vendor_data_csv_ingest_streaming_row_count_with_mocks() -> None:
    if not VENDOR_DATA_CSV.is_file():
        pytest.skip(f"Missing {VENDOR_DATA_CSV}")
    with VENDOR_DATA_CSV.open(encoding="utf-8") as f:
        expected = max(0, sum(1 for _ in f) - 1)
    emb = FakeTextEmbedder(vector=[0.0] * 768)
    store = FakeVectorStore()
    s = Settings(
        embedding_vector_size=768,
        qdrant_collection="large_csv_stream_test",
        ingest_upsert_batch_size=256,
    )
    n = ingest_vendor_csv(VENDOR_DATA_CSV, settings=s, embedder=emb, store=store)
    assert n == expected
    assert len(emb.calls) == expected
