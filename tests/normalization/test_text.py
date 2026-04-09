"""Tests for text normalization."""

import pytest

from vendor_lookup_rag.normalization import (
    compact_for_identifier_match,
    normalize_text,
    normalized_token_set,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  Acme Corp.  ", "acme corp"),
        ("Foo-Bar  Baz!", "foo bar baz"),
        ("VAT: DE1234567", "vat de1234567"),
        ("", ""),
        ("   ", ""),
    ],
)
def test_normalize_text_basic(raw: str, expected: str) -> None:
    assert normalize_text(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("foo\t\n  bar", "foo bar"),
        ("line1\r\nline2", "line1 line2"),
    ],
)
def test_normalize_text_tabs_and_newlines(raw: str, expected: str) -> None:
    assert normalize_text(raw) == expected


def test_normalize_text_narrow_nbsp() -> None:
    # U+00A0 NO-BREAK SPACE between tokens
    assert normalize_text("acme\u00a0corp gmbh") == "acme corp gmbh"


def test_normalize_text_zero_width_becomes_word_boundary() -> None:
    # U+200B ZERO WIDTH SPACE → treated as a boundary (space), not glued tokens
    assert normalize_text("foo\u200bbar") == "foo bar"
    assert normalize_text("VAT\u200bDE123") == "vat de123"


def test_normalize_text_underscores_as_boundaries() -> None:
    assert normalize_text("vendor_id_acme") == "vendor id acme"
    assert normalize_text("foo___bar") == "foo bar"


def test_normalize_text_nfkc_fullwidth() -> None:
    # Fullwidth Latin letters/digits (compatibility) → usual forms, then lowercased
    assert normalize_text("ＡＣＭＥ　ＧｍｂＨ") == "acme gmbh"
    assert normalize_text("ＶＡＴ：　１２３") == "vat 123"


def test_normalize_text_mixed_script_letters_preserved() -> None:
    # Cyrillic letters remain as word characters (lowercased)
    assert normalize_text("ООО  Рога") == "ооо рога"


def test_normalized_token_set_matches_normalize_then_split() -> None:
    assert normalized_token_set("Foo-Bar  Baz!") == frozenset({"foo", "bar", "baz"})
    assert normalized_token_set("") == frozenset()
    assert normalized_token_set("acme corp") == frozenset({"acme", "corp"})


def test_normalized_token_set_idempotent_on_normalized_input() -> None:
    n = normalize_text("Acme-Berlin GmbH")
    assert normalized_token_set(n) == frozenset({"acme", "berlin", "gmbh"})


def test_compact_for_identifier_match() -> None:
    assert compact_for_identifier_match("DE 123 456") == "de123456"
    assert compact_for_identifier_match("") == ""
