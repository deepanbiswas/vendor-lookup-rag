"""Thin REST API layer (FastAPI) for the vendor lookup agent."""

from vendor_lookup_rag.api.main import app, create_app
from vendor_lookup_rag.api.openapi import get_openapi_schema

__all__ = ["app", "create_app", "get_openapi_schema"]
