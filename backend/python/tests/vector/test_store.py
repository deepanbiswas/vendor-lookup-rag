"""Tests for Qdrant vector store."""

import pytest
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from vendor_lookup_rag.models import VendorRecord
from vendor_lookup_rag.adapters.qdrant import QdrantVectorStore


def test_upsert_and_search_roundtrip() -> None:
    client = QdrantClient(":memory:")
    store = QdrantVectorStore(client, "vendors_test", vector_size=4)
    store.ensure_collection()
    rec = VendorRecord(vendor_id="a1", legal_name="Acme", city="Berlin")
    vec = [0.1, 0.0, 0.0, 0.0]
    store.upsert_vendor(vendor_id="a1", vector=vec, record=rec)
    hits = store.search(vec, limit=3)
    assert len(hits) == 1
    assert hits[0].record.vendor_id == "a1"
    assert hits[0].score >= 0.99


def test_upsert_batch_roundtrip_full_vendor_payload() -> None:
    client = QdrantClient(":memory:")
    store = QdrantVectorStore(client, "vendors_batch", vector_size=3)
    store.ensure_collection()
    rec = VendorRecord(
        vendor_id="b1",
        legal_name="Acme GmbH",
        secondary_name="Remittance line",
        company_code="CC9",
        address="Street 1",
        city="Berlin",
        postal_code="10115",
        state="BE",
        country="DE",
        vat_id="DE123",
        date_format="dd.mm.yyyy",
        eu_member_flag="Y",
        extras={"notes": "extra"},
    )
    vec = [0.0, 1.0, 0.0]
    store.upsert_vendors_batch([("b1", vec, rec)])
    hits = store.search(vec, limit=2)
    assert len(hits) == 1
    r = hits[0].record
    assert r.vendor_id == "b1"
    assert r.legal_name == "Acme GmbH"
    assert r.secondary_name == "Remittance line"
    assert r.company_code == "CC9"
    assert r.extras.get("notes") == "extra"


def test_ensure_collection_rejects_vector_size_mismatch() -> None:
    client = QdrantClient(":memory:")
    client.create_collection(
        "wrong_size",
        vectors_config=VectorParams(size=4, distance=Distance.COSINE),
    )
    store = QdrantVectorStore(client, "wrong_size", vector_size=8)
    with pytest.raises(RuntimeError, match="vector size"):
        store.ensure_collection()


def test_ensure_collection_rejects_non_cosine_distance() -> None:
    client = QdrantClient(":memory:")
    client.create_collection(
        "euclid_col",
        vectors_config=VectorParams(size=4, distance=Distance.EUCLID),
    )
    store = QdrantVectorStore(client, "euclid_col", vector_size=4)
    with pytest.raises(RuntimeError, match="distance"):
        store.ensure_collection()


def test_ensure_collection_idempotent() -> None:
    client = QdrantClient(":memory:")
    store = QdrantVectorStore(client, "idemp", vector_size=2)
    store.ensure_collection()
    store.ensure_collection()
    store.upsert_vendor(vendor_id="x", vector=[1.0, 0.0], record=VendorRecord(vendor_id="x", legal_name="Co"))
