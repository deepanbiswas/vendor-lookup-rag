"""Tests for CSV loading."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from vendor_lookup_rag.csv import (
    ColumnMapping,
    DEFAULT_COLUMN_MAPPING,
    iter_vendor_csv,
    load_column_mapping_from_json,
    load_vendor_csv,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_iter_vendor_csv_matches_load_vendor_csv() -> None:
    p = FIXTURES / "sample_vendors.csv"
    streamed = [rec for _, rec in iter_vendor_csv(p)]
    loaded = load_vendor_csv(p)
    assert streamed == loaded


def test_utf8_bom_stripped_from_first_column_header(tmp_path: Path) -> None:
    p = tmp_path / "bom.csv"
    p.write_bytes(b"\xef\xbb\xbfvendor_id,legal_name\nx1,Acme\n")
    rows = load_vendor_csv(p)
    assert rows[0].vendor_id == "x1"
    assert rows[0].legal_name == "Acme"


def test_iter_vendor_csv_row_numbers_start_at_two() -> None:
    pairs = list(iter_vendor_csv(FIXTURES / "sample_vendors.csv"))
    assert pairs[0][0] == 2
    assert pairs[1][0] == 3


def test_load_sample_csv() -> None:
    rows = load_vendor_csv(FIXTURES / "sample_vendors.csv")
    assert len(rows) == 2
    assert rows[0].vendor_id == "v-001"
    assert rows[0].legal_name == "Acme Tools GmbH"
    assert rows[0].city == "Berlin"
    assert rows[1].vat_id == "GB987654321"


def test_load_vendor_data_style_headers() -> None:
    rows = load_vendor_csv(FIXTURES / "vendor_data_style.csv")
    assert len(rows) == 1
    r = rows[0]
    assert r.vendor_id == "v-001"
    assert r.legal_name == "Acme GmbH"
    assert r.secondary_name == "Remittance line"
    assert r.company_code == "CC1"
    assert r.address == "Street 1"
    assert r.city == "Berlin"
    assert r.postal_code == "10115"
    assert r.state == "BE"
    assert r.country == "DE"
    assert r.vat_id == "DE123456789"
    assert r.date_format == "dd.mm.yyyy"
    assert r.eu_member_flag == "Y"
    assert "notes" in r.extras
    assert r.extras["notes"] == "unmapped column"
    assert "acme" in r.embedding_text().lower()


def test_custom_mapping_json_override(tmp_path: Path) -> None:
    csv_path = tmp_path / "m.csv"
    csv_path.write_text(
        "id_x,display_name,city\n"
        "a1,Widget Inc,Munich\n",
        encoding="utf-8",
    )
    map_path = tmp_path / "map.json"
    map_path.write_text(
        json.dumps(
            {
                "vendor_id": ["id_x"],
                "legal_name": ["display_name"],
                "city": ["city"],
            }
        ),
        encoding="utf-8",
    )
    m = load_column_mapping_from_json(map_path)
    rows = load_vendor_csv(csv_path, mapping=m)
    assert len(rows) == 1
    assert rows[0].vendor_id == "a1"
    assert rows[0].legal_name == "Widget Inc"
    assert rows[0].city == "Munich"


def test_default_mapping_includes_legacy_headers() -> None:
    assert "legal_name" in DEFAULT_COLUMN_MAPPING.legal_name
    assert "zip" in DEFAULT_COLUMN_MAPPING.postal_code


def test_missing_required_column(tmp_path: Path) -> None:
    p = tmp_path / "bad.csv"
    p.write_text("foo,bar\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing required column for"):
        load_vendor_csv(p)


def test_empty_required_field_row(tmp_path: Path) -> None:
    p = tmp_path / "empty.csv"
    p.write_text(
        "vendor_id,legal_name\n"
        "x1,\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Row 2"):
        load_vendor_csv(p)


def test_column_mapping_rejects_empty_vendor_id_list() -> None:
    with pytest.raises(ValidationError):
        ColumnMapping(vendor_id=[], legal_name=["legal_name"])
