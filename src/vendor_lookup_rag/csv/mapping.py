"""Configurable CSV column mapping for vendor master rows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from vendor_lookup_rag.models.records import VendorRecord


class ColumnMapping(BaseModel):
    """
    Logical field → ordered candidate CSV header names (case-insensitive).
    First non-empty cell wins for that field.
    """

    model_config = ConfigDict(frozen=True, extra="ignore")

    vendor_id: list[str] = Field(
        ...,
        description="At least one header name; required.",
    )
    legal_name: list[str] = Field(
        ...,
        description="At least one header name; required.",
    )
    secondary_name: list[str] = Field(default_factory=list)
    company_code: list[str] = Field(default_factory=list)
    address: list[str] = Field(default_factory=list)
    city: list[str] = Field(default_factory=list)
    postal_code: list[str] = Field(default_factory=list)
    state: list[str] = Field(default_factory=list)
    country: list[str] = Field(default_factory=list)
    vat_id: list[str] = Field(default_factory=list)
    date_format: list[str] = Field(default_factory=list)
    eu_member_flag: list[str] = Field(default_factory=list)

    @field_validator(
        "vendor_id",
        "legal_name",
        "secondary_name",
        "company_code",
        "address",
        "city",
        "postal_code",
        "state",
        "country",
        "vat_id",
        "date_format",
        "eu_member_flag",
        mode="before",
    )
    @classmethod
    def _normalize_header_lists(cls, v: Any) -> list[str]:
        if not isinstance(v, list):
            raise TypeError("expected a list of header name strings")
        return [str(x).lower().strip() for x in v if str(x).strip()]

    @field_validator("vendor_id", "legal_name")
    @classmethod
    def _required_lists_nonempty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("must list at least one candidate column")
        return v


def _reserved_header_keys(mapping: ColumnMapping) -> set[str]:
    keys: set[str] = set()
    for name in ColumnMapping.model_fields:
        vals = getattr(mapping, name)
        if isinstance(vals, list):
            keys.update(vals)
    return keys


def _first_nonempty(raw: dict[str, str], candidates: list[str]) -> str | None:
    for c in candidates:
        v = (raw.get(c) or "").strip()
        if v:
            return v
    return None


def row_to_vendor_record(raw: dict[str, str], mapping: ColumnMapping) -> VendorRecord:
    """
    Build a VendorRecord from a row dict with lowercased header keys.
    Unmapped non-empty columns are stored in extras.
    """
    reserved = _reserved_header_keys(mapping)
    vendor_id = _first_nonempty(raw, mapping.vendor_id)
    legal_name = _first_nonempty(raw, mapping.legal_name)
    if not vendor_id:
        raise ValueError("missing required vendor_id (no non-empty value in mapped columns)")
    if not legal_name:
        raise ValueError("missing required legal_name (no non-empty value in mapped columns)")

    extras: dict[str, str] = {}
    for k, v in raw.items():
        if k in reserved:
            continue
        vv = (v or "").strip()
        if vv:
            extras[k] = vv

    return VendorRecord(
        vendor_id=vendor_id,
        legal_name=legal_name,
        secondary_name=_first_nonempty(raw, mapping.secondary_name),
        company_code=_first_nonempty(raw, mapping.company_code),
        address=_first_nonempty(raw, mapping.address),
        city=_first_nonempty(raw, mapping.city),
        postal_code=_first_nonempty(raw, mapping.postal_code),
        state=_first_nonempty(raw, mapping.state),
        country=_first_nonempty(raw, mapping.country),
        vat_id=_first_nonempty(raw, mapping.vat_id),
        date_format=_first_nonempty(raw, mapping.date_format),
        eu_member_flag=_first_nonempty(raw, mapping.eu_member_flag),
        extras=extras,
    )


DEFAULT_COLUMN_MAPPING = ColumnMapping(
    vendor_id=["vendor_id", "supplier_id", "vendor_number"],
    legal_name=["legal_name", "name_1", "company_name", "supplier_name"],
    secondary_name=["name_2", "dba", "secondary_name"],
    company_code=["company_code", "co_code", "company"],
    address=["address", "street", "addr"],
    city=["city", "town"],
    postal_code=["postal_code", "zip", "zip_code", "postcode"],
    state=["state", "region", "province"],
    country=["country", "nation"],
    vat_id=["vat_id", "vat", "vat_no", "tax_id"],
    date_format=["date_format"],
    eu_member_flag=["eu_member_flag", "eu_member"],
)


def load_column_mapping_from_json(path: str | Path) -> ColumnMapping:
    """Merge JSON overrides with DEFAULT_COLUMN_MAPPING (per-key replacement)."""
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("column map JSON must be an object")
    merged = {**DEFAULT_COLUMN_MAPPING.model_dump(), **data}
    return ColumnMapping.model_validate(merged)
