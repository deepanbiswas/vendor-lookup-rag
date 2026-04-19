"""OpenAPI schema generation (offline, no external services)."""

from __future__ import annotations

import json

from vendor_lookup_rag.api.main import create_app
from vendor_lookup_rag.api.openapi import get_openapi_schema


def test_openapi_schema_is_swagger_compatible_oas3() -> None:
    schema = get_openapi_schema()
    assert schema["openapi"].startswith("3.")
    assert "/v1/health" in schema["paths"]
    assert "/v1/status" in schema["paths"]
    assert "/v1/chat" in schema["paths"]
    post = schema["paths"]["/v1/chat"]["post"]
    assert post["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("ChatRequest")
    assert "ChatResponse" in json.dumps(schema["components"]["schemas"])


def test_openapi_matches_app_openapi() -> None:
    app = create_app()
    assert get_openapi_schema(app) == app.openapi()
