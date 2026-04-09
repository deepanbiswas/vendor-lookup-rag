"""Vector store port for vendor embedding search and upsert."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from vendor_lookup_rag.models.records import SearchHit, VendorRecord


class VectorStore(Protocol):
    """Abstract vector index for vendor records (cosine similarity search)."""

    def ensure_collection(self) -> None: ...

    def upsert_vendor(self, *, vendor_id: str, vector: list[float], record: VendorRecord) -> None: ...

    def upsert_vendors_batch(
        self,
        items: Sequence[tuple[str, list[float], VendorRecord]],
    ) -> None: ...

    def search(self, vector: list[float], limit: int) -> list[SearchHit]: ...
