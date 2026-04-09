"""CLI entry for vendor CSV ingestion."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from vendor_lookup_rag.config import get_column_mapping, get_settings
from vendor_lookup_rag.csv import iter_vendor_csv
from vendor_lookup_rag.ingestion.pipeline import ingest_vendor_csv
from vendor_lookup_rag.observability import configure_app_logging

_logger = logging.getLogger(__name__)


def _dry_run(csv_path: str) -> int:
    s = get_settings()
    path = Path(csv_path)
    n = sum(1 for _ in iter_vendor_csv(path, mapping=get_column_mapping(s)))
    print(f"Dry run: {n} rows parsed (no embedding or Qdrant).", file=sys.stderr)
    return n


def main() -> None:
    p = argparse.ArgumentParser(description="Ingest vendor master CSV into Qdrant.")
    p.add_argument("csv_path", help="Path to vendor master CSV")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse CSV only; do not call Ollama or Qdrant.",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Log ingest progress to stderr (see --progress-every).",
    )
    p.add_argument(
        "--progress-every",
        type=int,
        default=500,
        metavar="N",
        help="With --verbose, log every N rows completed (default: 500). Use 0 to disable.",
    )
    args = p.parse_args()
    get_settings.cache_clear()
    configure_app_logging(get_settings())
    try:
        if args.dry_run:
            _dry_run(args.csv_path)
            sys.exit(0)
        n = ingest_vendor_csv(
            args.csv_path,
            verbose=args.verbose,
            progress_every=args.progress_every,
        )
        print(f"Ingested {n} vendor rows.", file=sys.stderr)
    except Exception as e:
        _logger.exception("vendor-ingest failed: %s", e)
        print(f"vendor-ingest: error: {e}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
