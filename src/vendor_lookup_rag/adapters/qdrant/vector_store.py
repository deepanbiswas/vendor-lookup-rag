"""Qdrant implementation of :class:`~vendor_lookup_rag.ports.vector_store.VectorStore`."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence

from qdrant_client import QdrantClient

_logger = logging.getLogger(__name__)
from qdrant_client.models import Distance, PointStruct, VectorParams

from vendor_lookup_rag.models.records import SearchHit, VendorRecord


def _point_id(vendor_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"vendor:{vendor_id}"))


class QdrantVectorStore:
    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        vector_size: int,
    ) -> None:
        self._client = client
        self._collection = collection_name
        self._vector_size = vector_size

    def _validate_existing_collection(self) -> None:
        info = self._client.get_collection(self._collection)
        vectors = info.config.params.vectors
        if not isinstance(vectors, VectorParams):
            raise RuntimeError(
                f"Collection {self._collection!r} uses unsupported vector config "
                f"(expected a single unnamed vector). Got {type(vectors).__name__}."
            )
        if vectors.size != self._vector_size:
            raise RuntimeError(
                f"Collection {self._collection!r} has vector size {vectors.size}, "
                f"but settings expect {self._vector_size}. Delete the collection, or align "
                f"EMBEDDING_VECTOR_SIZE with the model (see .env.example)."
            )
        if vectors.distance != Distance.COSINE:
            raise RuntimeError(
                f"Collection {self._collection!r} uses distance {vectors.distance!r}, "
                f"expected Cosine. Delete the collection or use one created by this app."
            )

    def ensure_collection(self) -> None:
        names = {c.name for c in self._client.get_collections().collections}
        if self._collection not in names:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=self._vector_size, distance=Distance.COSINE),
            )
            _logger.info(
                "Created Qdrant collection %r (vector_size=%s, distance=cosine)",
                self._collection,
                self._vector_size,
            )
            return
        self._validate_existing_collection()

    def upsert_vendor(self, *, vendor_id: str, vector: list[float], record: VendorRecord) -> None:
        self.upsert_vendors_batch([(vendor_id, vector, record)])

    def upsert_vendors_batch(
        self,
        items: Sequence[tuple[str, list[float], VendorRecord]],
    ) -> None:
        """Upsert many vendors in one Qdrant request (empty list is a no-op)."""
        if not items:
            return
        points = [
            PointStruct(
                id=_point_id(vid),
                vector=vec,
                payload=rec.model_dump(),
            )
            for vid, vec, rec in items
        ]
        self._client.upsert(
            collection_name=self._collection,
            points=points,
        )

    def search(self, vector: list[float], limit: int) -> list[SearchHit]:
        res = self._client.query_points(
            collection_name=self._collection,
            query=vector,
            limit=limit,
            with_payload=True,
        )
        out: list[SearchHit] = []
        for h in res.points:
            if h.payload is None:
                continue
            out.append(
                SearchHit(
                    score=float(h.score or 0.0),
                    record=VendorRecord.model_validate(h.payload),
                )
            )
        return out
