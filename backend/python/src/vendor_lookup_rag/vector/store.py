"""Backward-compatible vector store exports (implementation lives under ``adapters``)."""

from vendor_lookup_rag.adapters.qdrant.vector_store import QdrantVectorStore

# Historical name; same class as :class:`QdrantVectorStore`.
VendorVectorStore = QdrantVectorStore

__all__ = ["QdrantVectorStore", "VendorVectorStore"]
