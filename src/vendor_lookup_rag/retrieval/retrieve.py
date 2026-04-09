"""Vendor retrieval: normalize query, embed, search Qdrant."""

from __future__ import annotations

import logging
import time

from vendor_lookup_rag.config import Settings, get_settings

_logger = logging.getLogger(__name__)
from vendor_lookup_rag.models import SearchHit
from vendor_lookup_rag.normalization import normalize_text
from vendor_lookup_rag.ports import TextEmbedder, VectorStore
from vendor_lookup_rag.telemetry import emit_retrieval_event


def retrieve_vendors(
    query: str,
    *,
    embedder: TextEmbedder,
    store: VectorStore,
    settings: Settings | None = None,
    min_score: float | None = None,
) -> list[SearchHit]:
    """
    Normalize query, embed with Ollama, return top-K hits from Qdrant.

    ``min_score`` overrides :attr:`Settings.retrieval_min_score` when provided; use either
    to drop weak matches by cosine score before returning (classification may still apply).
    """
    s = settings or get_settings()
    t0 = time.perf_counter()
    normalized = normalize_text(query)
    if not normalized:
        _logger.warning("Vendor retrieval skipped: empty or whitespace-only query.")
        emit_retrieval_event(
            s,
            {
                "event": "vendor_retrieval",
                "phase": "complete",
                "skipped": "empty_query",
                "total_ms": round((time.perf_counter() - t0) * 1000, 3),
            },
        )
        return []

    t_embed = time.perf_counter()
    try:
        vector = embedder.embed(normalized)
    except Exception as e:
        _logger.exception("Embedding failed for vendor retrieval: %s", e)
        raise RuntimeError(
            "Failed to compute embedding for vendor search. "
            "Check Ollama is running and EMBEDDING_MODEL is pulled."
        ) from e
    embed_ms = round((time.perf_counter() - t_embed) * 1000, 3)

    t_search = time.perf_counter()
    try:
        hits = store.search(vector, limit=s.retrieval_top_k)
    except Exception as e:
        _logger.exception("Vector store search failed: %s", e)
        raise RuntimeError(
            "Failed to search Qdrant for vendors. Check QDRANT_URL and collection."
        ) from e
    search_ms = round((time.perf_counter() - t_search) * 1000, 3)

    floor = min_score if min_score is not None else s.retrieval_min_score
    raw_count = len(hits)
    if floor is not None:
        hits = [h for h in hits if h.score >= floor]
    filtered_count = len(hits)

    total_ms = round((time.perf_counter() - t0) * 1000, 3)
    emit_retrieval_event(
        s,
        {
            "event": "vendor_retrieval",
            "phase": "complete",
            "embed_ms": embed_ms,
            "search_ms": search_ms,
            "total_ms": total_ms,
            "top_k": s.retrieval_top_k,
            "hit_count_raw": raw_count,
            "hit_count": filtered_count,
            "min_score": floor,
        },
    )
    _logger.info(
        "Vendor retrieval complete top_k=%s raw_hits=%s after_min_score=%s total_ms=%s",
        s.retrieval_top_k,
        raw_count,
        filtered_count,
        total_ms,
    )

    return hits
