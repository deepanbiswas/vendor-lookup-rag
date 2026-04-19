"""OpenAPI (Swagger UI–compatible) schema for the Vendor Lookup API.

When the server runs, FastAPI serves the same document at ``GET /openapi.json`` and interactive
docs at ``GET /docs``. This module supports **offline** generation (no Ollama/Qdrant) for CI or
checked-in artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from vendor_lookup_rag.api.main import create_app


def get_openapi_schema(app: FastAPI | None = None) -> dict[str, Any]:
    """
    Build the OpenAPI 3.x schema dict (OpenAPI Initiative format; consumable by Swagger UI).

    Does not connect to external services: route metadata and Pydantic models are introspected only.
    """
    app = app or create_app()
    return app.openapi()


def write_openapi_json(path: Path | str, *, app: FastAPI | None = None) -> None:
    """Serialize :func:`get_openapi_schema` to a UTF-8 JSON file."""
    schema = get_openapi_schema(app=app)
    text = json.dumps(schema, indent=2, ensure_ascii=False) + "\n"
    Path(path).write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Emit OpenAPI JSON for the Vendor Lookup API (Swagger-compatible).",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        help="Write to this file instead of stdout.",
    )
    args = parser.parse_args()
    text = json.dumps(get_openapi_schema(), indent=2, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
