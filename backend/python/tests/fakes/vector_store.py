"""In-memory :class:`~vendor_lookup_rag.ports.vector_store.VectorStore` for tests."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from vendor_lookup_rag.models.records import SearchHit, VendorRecord


class FakeVectorStore:
    def __init__(
        self,
        search_hits: list[SearchHit] | None = None,
        *,
        on_search: Callable[[list[float], int], list[SearchHit]] | None = None,
        search_side_effect: BaseException | None = None,
    ) -> None:
        self._fixed_hits = list(search_hits) if search_hits is not None else []
        self._on_search = on_search
        self._search_side_effect = search_side_effect
        self.ensure_collection_calls = 0
        self.upsert_batches: list[list[tuple[str, list[float], VendorRecord]]] = []
        self.search_calls: list[tuple[list[float], int]] = []

    def ensure_collection(self) -> None:
        self.ensure_collection_calls += 1

    def upsert_vendor(self, *, vendor_id: str, vector: list[float], record: VendorRecord) -> None:
        self.upsert_vendors_batch([(vendor_id, vector, record)])

    def upsert_vendors_batch(
        self,
        items: Sequence[tuple[str, list[float], VendorRecord]],
    ) -> None:
        if items:
            self.upsert_batches.append(list(items))

    def search(self, vector: list[float], limit: int) -> list[SearchHit]:
        self.search_calls.append((list(vector), limit))
        if self._search_side_effect is not None:
            raise self._search_side_effect
        if self._on_search is not None:
            return self._on_search(vector, limit)
        return list(self._fixed_hits[:limit])
