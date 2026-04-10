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


def _hits_meeting_partial_floor(hits: list[SearchHit], score_partial: float) -> list[SearchHit]:
    """Drop retrieval tail below the partial cosine bar (list stays score-sorted)."""
    return [h for h in hits if h.score >= score_partial]


def classify_matches(
    *,
    normalized_query: str,
    hits: list[SearchHit],
    score_exact: float,
    score_partial: float,
) -> MatchResult:
    """
    Classify top retrieval hits using score thresholds and optional VAT/name equality.

    Expects ``normalized_query`` from ``normalize_text`` (same rules as retrieval).

    Exact: top score >= score_exact and (VAT/company code in query or token overlap on
    legal + secondary + company code fields).

    Partial: top score >= score_partial.

    Otherwise none.

    For **exact** and **partial**, returned ``hits`` only include rows with
    ``score >= score_partial`` so the tool does not list weak tail matches. For **none**,
    candidates are omitted (empty list).
    """
    if not hits:
        return MatchResult(
            kind=MatchKind.NONE,
            hits=[],
            message="No matching vendors found. Flag for manual verification.",
        )

    top = hits[0]
    query_compact = _query_compact(normalized_query)
    id_hit = _identifier_in_query(top.record, query_compact)
    name_overlap = _name_overlap(normalized_query, top.record)
    at_partial = _hits_meeting_partial_floor(hits, score_partial)

    if top.score >= score_exact and (id_hit or name_overlap):
        return MatchResult(
            kind=MatchKind.EXACT,
            hits=at_partial,
            message="Exact match — displaying vendor details.",
        )
    if top.score >= score_partial:
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
