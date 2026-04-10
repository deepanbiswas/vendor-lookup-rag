"""Vendor lookup tool body: retrieval + classification (no LLM framework imports)."""

from __future__ import annotations

import logging
import time

from vendor_lookup_rag.agent.deps import AgentDeps
from vendor_lookup_rag.config import Settings

_logger = logging.getLogger(__name__)
from vendor_lookup_rag.matching import classify_matches
from vendor_lookup_rag.models import (
    SearchHit,
    SearchVendorCandidate,
    SearchVendorToolError,
    SearchVendorToolResult,
    SearchVendorToolSuccess,
)
from vendor_lookup_rag.normalization import normalize_text
from vendor_lookup_rag.retrieval import retrieve_vendors
from vendor_lookup_rag.telemetry import emit_agent_tool_event

SYSTEM_PROMPT = """You help invoice processors verify vendors against a master list.
Always call the search_vendors tool with the user's vendor-related question or details.
Summarize the tool result clearly: if exact match, confirm; if partial, list options; if none, say no match and suggest manual review."""


def _hit_to_candidate(h: SearchHit) -> SearchVendorCandidate:
    r = h.record
    return SearchVendorCandidate(
        score=h.score,
        vendor_id=r.vendor_id,
        legal_name=r.legal_name,
        secondary_name=r.secondary_name,
        company_code=r.company_code,
        city=r.city,
        vat_id=r.vat_id,
    )


def _retrieval_score_floor(settings: Settings) -> float:
    """Do not retrieve or return candidates below the partial threshold (and respect RETRIEVAL_MIN_SCORE)."""
    p = settings.score_threshold_partial
    r = settings.retrieval_min_score
    if r is not None:
        return max(p, r)
    return p


def search_vendors_tool_body(deps: AgentDeps, user_query: str) -> SearchVendorToolResult:
    """
    Run retrieval + classification; return a structured result for the chat model.

    Used by the ``search_vendors`` tool and unit-tested with mocks.
    """
    t0 = time.perf_counter()
    settings = deps.settings
    try:
        hits = retrieve_vendors(
            user_query,
            embedder=deps.embedder,
            store=deps.store,
            settings=settings,
            min_score=_retrieval_score_floor(settings),
        )
    except RuntimeError as e:
        _logger.error("search_vendors tool retrieval failed: %s", e)
        err = SearchVendorToolError(
            error="retrieval_failed",
            message=str(e),
            detail=None,
        )
        emit_agent_tool_event(
            settings,
            {
                "phase": "error",
                "error": err.error,
                "total_ms": round((time.perf_counter() - t0) * 1000, 3),
            },
        )
        return err

    nq = normalize_text(user_query)
    match = classify_matches(
        normalized_query=nq,
        hits=hits,
        score_exact=settings.score_threshold_exact,
        score_partial=settings.score_threshold_partial,
    )
    out = SearchVendorToolSuccess(
        kind=match.kind.value,
        message=match.message,
        candidates=[_hit_to_candidate(h) for h in match.hits],
    )
    emit_agent_tool_event(
        settings,
        {
            "phase": "complete",
            "kind": out.kind,
            "candidate_count": len(out.candidates),
            "total_ms": round((time.perf_counter() - t0) * 1000, 3),
        },
    )
    _logger.info(
        "search_vendors tool ok kind=%s candidates=%s",
        out.kind,
        len(out.candidates),
    )
    return out
