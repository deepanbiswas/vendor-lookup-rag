"""Load vendor master CSV into validated records."""

import csv
from collections.abc import Iterator
from pathlib import Path

from vendor_lookup_rag.csv.mapping import (
    DEFAULT_COLUMN_MAPPING,
    ColumnMapping,
    row_to_vendor_record,
)
from vendor_lookup_rag.models.records import VendorRecord


def _field_key(name: str) -> str:
    """Normalize CSV header / row keys (lowercase, strip, remove UTF-8 BOM)."""
    return name.replace("\ufeff", "").lower().strip()


def _validate_header_for_mapping(header_lower: set[str], mapping: ColumnMapping) -> None:
    for field in ("vendor_id", "legal_name"):
        candidates = getattr(mapping, field)
        if not header_lower.intersection(candidates):
            raise ValueError(
                f"Missing required column for '{field}': need one of {candidates}; "
                f"found headers {sorted(header_lower)}",
            )


def iter_vendor_csv(
    path: str | Path,
    *,
    encoding: str = "utf-8",
    mapping: ColumnMapping | None = None,
) -> Iterator[tuple[int, VendorRecord]]:
    """
    Stream CSV rows as ``(row_number, VendorRecord)`` without loading the file into memory.

    ``row_number`` is the 1-based data row index in the file (line 1 is the header; first
    data row is 2), matching error messages from :func:`load_vendor_csv`.
    """
    m = mapping or DEFAULT_COLUMN_MAPPING
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(p)

    with p.open(newline="", encoding=encoding) as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV has no header row")
        header_lower = {_field_key(h) for h in reader.fieldnames if h}
        _validate_header_for_mapping(header_lower, m)

        for i, row in enumerate(reader, start=2):
            raw = {_field_key(k): (v or "").strip() for k, v in row.items() if k}
            try:
                rec = row_to_vendor_record(raw, m)
            except ValueError as e:
                raise ValueError(f"Row {i}: {e}") from e
            yield i, rec


def load_vendor_csv(
    path: str | Path,
    *,
    encoding: str = "utf-8",
    mapping: ColumnMapping | None = None,
) -> list[VendorRecord]:
    """
    Read a CSV and map columns to VendorRecord using ``mapping``.

    Required logical fields (via mapping): ``vendor_id``, ``legal_name``.
    Other columns follow the mapping; unmapped non-empty columns go to ``extras``.

    For large files, prefer :func:`iter_vendor_csv` or :func:`ingest_vendor_csv` (streaming).
    """
    return [rec for _, rec in iter_vendor_csv(path, encoding=encoding, mapping=mapping)]
