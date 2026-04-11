"""Thin REST API layer (FastAPI) for the vendor lookup agent."""

from vendor_lookup_rag.api.main import app, create_app

__all__ = ["app", "create_app"]
