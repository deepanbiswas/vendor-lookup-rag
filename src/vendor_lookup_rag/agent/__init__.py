"""Vendor lookup agent: deps, tool logic, and default Pydantic AI runner."""

from __future__ import annotations

from typing import Any

from vendor_lookup_rag.agent.deps import AgentDeps
from vendor_lookup_rag.agent.runner import search_vendors_tool_body

__all__ = ["AgentDeps", "build_vendor_agent", "search_vendors_tool_body"]


def __getattr__(name: str) -> Any:
    if name == "build_vendor_agent":
        from vendor_lookup_rag.adapters.pydantic_ai import build_vendor_agent as _build

        return _build
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
