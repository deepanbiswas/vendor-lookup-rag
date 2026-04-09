"""Integration: real Ollama embed + Qdrant search for retrieve_vendors."""

from __future__ import annotations

import uuid

import pytest
from qdrant_client import QdrantClient

from vendor_lookup_rag.config import Settings, get_settings
from vendor_lookup_rag.adapters.ollama import OllamaEmbedder
from vendor_lookup_rag.adapters.qdrant import QdrantVectorStore
from vendor_lookup_rag.models import VendorRecord
from vendor_lookup_rag.normalization import normalize_text
from vendor_lookup_rag.retrieval import retrieve_vendors


@pytest.mark.integration
@pytest.mark.requires_ollama
def test_retrieve_vendors_live_after_upsert(
    skip_if_no_qdrant: None,
    skip_if_no_ollama: None,
    qdrant_url: str,
) -> None:
    s = get_settings()
    name = f"retrieval_e2e_{uuid.uuid4().hex[:10]}"
    client = QdrantClient(url=qdrant_url)
    store = QdrantVectorStore(client, name, s.embedding_vector_size)
    emb = OllamaEmbedder(s.ollama_base_url, s.embedding_model)
    try:
        store.ensure_collection()
        rec = VendorRecord(vendor_id="e2e-1", legal_name="Retrieval Test Vendor GmbH Berlin")
        vec = emb.embed(normalize_text(rec.embedding_text()))
        store.upsert_vendor(vendor_id=rec.vendor_id, vector=vec, record=rec)
        rs = Settings(
            retrieval_top_k=5,
            qdrant_url=qdrant_url,
            qdrant_collection=name,
            embedding_vector_size=s.embedding_vector_size,
            ollama_base_url=s.ollama_base_url,
            embedding_model=s.embedding_model,
        )
        hits = retrieve_vendors(
            "Retrieval Test Vendor Berlin",
            embedder=emb,
            store=store,
            settings=rs,
        )
        assert hits
        assert any(h.record.vendor_id == "e2e-1" for h in hits)
    finally:
        emb.close()
        try:
            client.delete_collection(collection_name=name)
        except Exception:
            pass
