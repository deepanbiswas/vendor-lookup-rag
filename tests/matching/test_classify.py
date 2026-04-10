"""Tests for match classification."""

from vendor_lookup_rag.matching import MatchKind, classify_matches
from vendor_lookup_rag.models import SearchHit, VendorRecord
from vendor_lookup_rag.normalization import normalize_text


def _nq(s: str) -> str:
    """Mirror agent path: queries are normalized before ``classify_matches``."""
    return normalize_text(s)


def _hit(
    score: float,
    vid: str = "v1",
    name: str = "Acme GmbH",
    vat: str | None = "DE123",
    *,
    secondary_name: str | None = None,
    company_code: str | None = None,
) -> SearchHit:
    return SearchHit(
        score=score,
        record=VendorRecord(
            vendor_id=vid,
            legal_name=name,
            vat_id=vat,
            secondary_name=secondary_name,
            company_code=company_code,
        ),
    )


def test_no_hits() -> None:
    r = classify_matches(
        normalized_query=_nq("acme"),
        hits=[],
        score_exact=0.9,
        score_partial=0.5,
    )
    assert r.kind == MatchKind.NONE
    assert "manual" in r.message.lower()


def test_exact_high_score_and_name_overlap() -> None:
    hits = [_hit(0.95, name="Acme Berlin GmbH")]
    r = classify_matches(
        normalized_query=_nq("acme berlin gmbh"),
        hits=hits,
        score_exact=0.92,
        score_partial=0.55,
    )
    assert r.kind == MatchKind.EXACT


def test_exact_via_vat_in_query() -> None:
    hits = [_hit(0.93, vat="DE999")]
    r = classify_matches(
        normalized_query=_nq("de999 something"),
        hits=hits,
        score_exact=0.92,
        score_partial=0.55,
    )
    assert r.kind == MatchKind.EXACT


def test_exact_via_company_code_in_query() -> None:
    hits = [_hit(0.93, name="Other Corp", vat=None, company_code="AB12")]
    r = classify_matches(
        normalized_query=_nq("please check AB12 vendor"),
        hits=hits,
        score_exact=0.92,
        score_partial=0.55,
    )
    assert r.kind == MatchKind.EXACT


def test_exact_overlap_on_secondary_name_only() -> None:
    hits = [
        _hit(
            0.95,
            name="Unknown Holding GmbH",
            secondary_name="Widget Works Berlin",
            vat=None,
        )
    ]
    r = classify_matches(
        normalized_query=_nq("widget works berlin office"),
        hits=hits,
        score_exact=0.92,
        score_partial=0.55,
    )
    assert r.kind == MatchKind.EXACT


def test_hyphenated_legal_name_aligns_with_normalized_query_tokens() -> None:
    hits = [_hit(0.95, name="Foo-Bar Baz GmbH")]
    r = classify_matches(
        normalized_query=_nq("foo bar baz gmbh"),
        hits=hits,
        score_exact=0.92,
        score_partial=0.55,
    )
    assert r.kind == MatchKind.EXACT


def test_partial_only() -> None:
    hits = [_hit(0.7, name="Other Corp")]
    r = classify_matches(
        normalized_query=_nq("unrelated query text here"),
        hits=hits,
        score_exact=0.92,
        score_partial=0.55,
    )
    assert r.kind == MatchKind.PARTIAL


def test_partial_drops_candidates_below_partial_threshold() -> None:
    """Only list rows at or above the partial cosine bar (sorted tail from Qdrant)."""
    hits = [
        _hit(0.72, vid="good", name="HYLAND ENTERPRISES INC"),
        _hit(0.54, vid="weak", name="HYCHEM INC"),
        _hit(0.40, vid="drop", name="OTHER"),
    ]
    r = classify_matches(
        normalized_query=_nq("hyland"),
        hits=hits,
        score_exact=0.92,
        score_partial=0.70,
    )
    assert r.kind == MatchKind.PARTIAL
    assert len(r.hits) == 1
    assert r.hits[0].record.vendor_id == "good"


def test_high_exact_score_without_overlap_is_partial_not_exact() -> None:
    """Conservative: cosine alone does not yield EXACT without id or token agreement."""
    hits = [_hit(0.97, name="Acme GmbH")]
    r = classify_matches(
        normalized_query=_nq("completely different words"),
        hits=hits,
        score_exact=0.92,
        score_partial=0.55,
    )
    assert r.kind == MatchKind.PARTIAL


def test_none_low_score() -> None:
    hits = [_hit(0.3)]
    r = classify_matches(
        normalized_query=_nq("foo"),
        hits=hits,
        score_exact=0.92,
        score_partial=0.55,
    )
    assert r.kind == MatchKind.NONE
    assert r.hits == []


def test_boundary_exact_threshold_inclusive() -> None:
    hits = [_hit(0.92, name="Acme Berlin GmbH")]
    r = classify_matches(
        normalized_query=_nq("acme berlin gmbh"),
        hits=hits,
        score_exact=0.92,
        score_partial=0.55,
    )
    assert r.kind == MatchKind.EXACT


def test_boundary_partial_threshold_inclusive() -> None:
    hits = [_hit(0.55, name="Other Corp")]
    r = classify_matches(
        normalized_query=_nq("no overlap here"),
        hits=hits,
        score_exact=0.92,
        score_partial=0.55,
    )
    assert r.kind == MatchKind.PARTIAL


def test_just_below_partial_threshold_is_none() -> None:
    hits = [_hit(0.549999, name="Other Corp")]
    r = classify_matches(
        normalized_query=_nq("no overlap"),
        hits=hits,
        score_exact=0.92,
        score_partial=0.55,
    )
    assert r.kind == MatchKind.NONE


def test_single_char_company_code_does_not_trigger_identifier_exact() -> None:
    hits = [_hit(0.93, name="Other Corp", vat=None, company_code="A")]
    r = classify_matches(
        normalized_query=_nq("something A something"),
        hits=hits,
        score_exact=0.92,
        score_partial=0.55,
    )
    assert r.kind == MatchKind.PARTIAL
