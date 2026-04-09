"""Batch ingestion: CSV → embeddings → Qdrant."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from qdrant_client import QdrantClient

from vendor_lookup_rag.adapters.factory import make_text_embedder, open_vector_store

_logger = logging.getLogger(__name__)
from vendor_lookup_rag.config import Settings, get_column_mapping, get_settings
from vendor_lookup_rag.csv import iter_vendor_csv
from vendor_lookup_rag.ports import TextEmbedder, VectorStore
from vendor_lookup_rag.models import VendorRecord
from vendor_lookup_rag.normalization import normalize_text


def ingest_vendor_csv(
    csv_path: str | Path,
    *,
    settings: Settings | None = None,
    embedder: TextEmbedder | None = None,
    store: VectorStore | None = None,
    client: QdrantClient | None = None,
    verbose: bool = False,
    progress_every: int = 500,
) -> int:
    """
    Load CSV, embed each vendor's text, upsert into Qdrant.

    Returns number of rows indexed.

    Reads the CSV in a **streaming** fashion (row-by-row) so memory stays bounded for
    large exports.

    If ``verbose`` is True and ``progress_every`` > 0, prints progress to stderr
    every ``progress_every`` rows completed.

    If ``store`` is provided, vectors are written through that :class:`~vendor_lookup_rag.ports.vector_store.VectorStore`
    implementation and ``client`` is not used to build the store (useful for tests and alternate backends).
    If ``store`` is omitted, a :class:`~vendor_lookup_rag.adapters.qdrant.QdrantVectorStore` is created from ``client``
    or a new :class:`~qdrant_client.QdrantClient` using settings.
    """
    s = settings or get_settings()
    path = Path(csv_path)
    _logger.info("Starting CSV ingest path=%s", path.resolve())
    mapping = get_column_mapping(s)
    batch_limit = s.ingest_upsert_batch_size

    if store is not None:
        vec_store = store
        own_client = False
        qc: QdrantClient | None = client
    else:
        handle = open_vector_store(s, client=client)
        vec_store = handle.store
        qc = handle.qdrant_client
        own_client = handle.own_client
    vec_store.ensure_collection()

    own_embedder = embedder is None
    emb = embedder or make_text_embedder(s)

    try:
        count = 0

        def maybe_progress() -> None:
            if verbose and progress_every > 0 and count % progress_every == 0:
                print(f"Ingest progress: {count} rows indexed.", file=sys.stderr)

        batch: list[tuple[str, list[float], VendorRecord]] = []
        for row_num, rec in iter_vendor_csv(path, mapping=mapping):
            text = normalize_text(rec.embedding_text())
            if not text:
                raise ValueError(
                    f"CSV row {row_num} (vendor_id={rec.vendor_id!r}): embedding text is empty "
                    "after normalization; fix or remove the row."
                )
            vec = emb.embed(text)
            batch.append((rec.vendor_id, vec, rec))
            if len(batch) >= batch_limit:
                vec_store.upsert_vendors_batch(batch)
                count += len(batch)
                batch.clear()
                maybe_progress()
        if batch:
            vec_store.upsert_vendors_batch(batch)
            count += len(batch)
            maybe_progress()
        _logger.info("CSV ingest finished rows=%s path=%s", count, path.resolve())
        return count
    finally:
        if own_embedder:
            closer = getattr(emb, "close", None)
            if callable(closer):
                closer()
        if own_client and qc is not None:
            qc.close()
