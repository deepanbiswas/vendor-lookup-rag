"""Classify retrieval results into exact / partial / no match."""

from enum import Enum

from pydantic import BaseModel

from vendor_lookup_rag.models.records import SearchHit, VendorRecord
from vendor_lookup_rag.normalization.text import compact_for_identifier_match, normalized_token_set


class MatchKind(str, Enum):
    EXACT = "exact"
    PARTIAL = "partial"
    NONE = "none"


class MatchResult(BaseModel):
    kind: MatchKind
    hits: list[SearchHit]
    message: str


def _vendor_tokens_for_overlap(record: VendorRecord) -> frozenset[str]:
    """Tokens from legal name, secondary name, and company code (Iteration 3 fields)."""
    tokens: set[str] = set()
    tokens.update(normalized_token_set(record.legal_name))
    if record.secondary_name:
        tokens.update(normalized_token_set(record.secondary_name))
    if record.company_code:
        tokens.update(normalized_token_set(record.company_code))
    return frozenset(tokens)


def _identifier_in_query(record: VendorRecord, query_compact: str) -> bool:
    """VAT or company code appears in the compact normalized query (substring)."""
    q = query_compact
    vat = compact_for_identifier_match(record.vat_id or "")
    if vat and vat in q:
        return True
    cc = compact_for_identifier_match(record.company_code or "")
    if cc and len(cc) >= 2 and cc in q:
        return True
    return False


def _query_compact(normalized_query: str) -> str:
    """Space-free compact form of an already-normalized query (for identifier substring checks)."""
    return normalized_query.replace(" ", "").lower()


def _name_overlap(normalized_query: str, record: VendorRecord) -> bool:
    query_tokens = normalized_token_set(normalized_query)
    vendor_tokens = _vendor_tokens_for_overlap(record)
    if not query_tokens:
        return False
    return len(query_tokens & vendor_tokens) >= 2 or (
        len(query_tokens) == 1 and query_tokens <= vendor_tokens
    )


def _hits_meeting_score_floor(hits: list[SearchHit], min_score: float) -> list[SearchHit]:
    """Keep hits at or above ``min_score`` (list stays score-sorted)."""
    return [h for h in hits if h.score >= min_score]


def _canonical_search_hits(hits: list[SearchHit]) -> list[SearchHit]:
    """
    Re-parse hits through this module's ``SearchHit`` so ``MatchResult`` validation
    succeeds after Streamlit reloads or mixed imports (``models`` vs ``models.records``).
    """
    return [SearchHit.model_validate(h.model_dump()) for h in hits]


def _effective_floors(score_exact: float, score_partial: float, score_tolerance: float) -> tuple[float, float]:
    """Cosine floors with optional tolerance band (clamped to [0, 1])."""
    fe = max(0.0, score_exact - score_tolerance)
    fp = max(0.0, score_partial - score_tolerance)
    return min(fe, 1.0), min(fp, 1.0)


def classify_matches(
    *,
    normalized_query: str,
    hits: list[SearchHit],
    score_exact: float,
    score_partial: float,
    score_tolerance: float = 0.0,
) -> MatchResult:
    """
    Classify top retrieval hits using score thresholds and optional VAT/name equality.

    Expects ``normalized_query`` from ``normalize_text`` (same rules as retrieval).

    ``score_tolerance`` widens acceptance: effective exact floor is
    ``max(0, score_exact - tolerance)``, partial floor ``max(0, score_partial - tolerance)``.

    Exact: top score >= effective exact floor and (VAT/company code in query or token overlap on
    legal + secondary + company code fields).

    Partial: top score >= effective partial floor (and exact rules did not apply).

    Otherwise none.

    Returned ``hits`` for exact/partial only include rows with
    ``score >= effective partial floor``. For **none**, candidates are omitted (empty list).
    """
    if not hits:
        return MatchResult(
            kind=MatchKind.NONE,
            hits=[],
            message="No matching vendors found. Flag for manual verification.",
        )

    hits = _canonical_search_hits(hits)

    floor_exact, floor_partial = _effective_floors(score_exact, score_partial, score_tolerance)

    top = hits[0]
    query_compact = _query_compact(normalized_query)
    id_hit = _identifier_in_query(top.record, query_compact)
    name_overlap = _name_overlap(normalized_query, top.record)
    at_partial = _hits_meeting_score_floor(hits, floor_partial)

    if top.score >= floor_exact and (id_hit or name_overlap):
        return MatchResult(
            kind=MatchKind.EXACT,
            hits=at_partial,
            message="Exact match — displaying vendor details.",
        )
    if top.score >= floor_partial:
        return MatchResult(
            kind=MatchKind.PARTIAL,
            hits=at_partial,
            message="Partial match — review suggested candidates below.",
        )
    return MatchResult(
        kind=MatchKind.NONE,
        hits=[],
        message="No confident match. Flag for manual verification.",
    )
