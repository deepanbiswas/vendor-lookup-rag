"""Optional integration tests (run when Qdrant/Ollama are up)."""

from __future__ import annotations

import uuid

import pytest
from qdrant_client import QdrantClient

from vendor_lookup_rag.models import VendorRecord
from vendor_lookup_rag.adapters.qdrant import QdrantVectorStore


@pytest.fixture
def qdrant_integration_store(
    skip_if_no_qdrant: None,
    qdrant_url: str,
) -> tuple[QdrantClient, QdrantVectorStore, str]:
    """Unique collection per test; deleted in teardown."""
    name = f"integration_vendors_{uuid.uuid4().hex[:12]}"
    client = QdrantClient(url=qdrant_url)
    store = QdrantVectorStore(client, name, vector_size=4)
    yield client, store, name
    try:
        client.delete_collection(collection_name=name)
    except Exception:
        pass


@pytest.mark.integration
def test_qdrant_ping(skip_if_no_qdrant: None, qdrant_url: str) -> None:
    c = QdrantClient(url=qdrant_url)
    c.get_collections()


@pytest.mark.integration
def test_qdrant_upsert_search_live(qdrant_integration_store: tuple[QdrantClient, QdrantVectorStore, str]) -> None:
    _client, store, _name = qdrant_integration_store
    store.ensure_collection()
    rec = VendorRecord(vendor_id="int-1", legal_name="Integration Co")
    vec = [1.0, 0.0, 0.0, 0.0]
    store.upsert_vendor(vendor_id="int-1", vector=vec, record=rec)
    hits = store.search(vec, limit=2)
    assert hits and hits[0].record.vendor_id == "int-1"
