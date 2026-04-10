"""Format vendor search tool results for Streamlit (structured markdown, no LLM prose)."""

from __future__ import annotations

import json
from typing import Any

from vendor_lookup_rag.models import SearchVendorCandidate, SearchVendorToolError, SearchVendorToolSuccess


def extract_search_vendors_tool_result(result: Any) -> SearchVendorToolSuccess | SearchVendorToolError | None:
    """
    Parse pydantic-ai ``new_messages_json`` for the last ``search_vendors`` tool return.

    Returns structured models when present; otherwise ``None`` (e.g. tool not called).
    """
    nm = getattr(result, "new_messages_json", None)
    if not callable(nm):
        return None
    try:
        raw = nm()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        msgs = json.loads(raw) if raw else []
    except (json.JSONDecodeError, TypeError, ValueError):
        return None

    last: SearchVendorToolSuccess | SearchVendorToolError | None = None
    for msg in msgs:
        parts = msg.get("parts") if isinstance(msg, dict) else None
        if not isinstance(parts, list):
            continue
        for part in parts:
            if not isinstance(part, dict):
                continue
            if part.get("part_kind") != "tool-return":
                continue
            if part.get("tool_name") != "search_vendors":
                continue
            content = part.get("content")
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    continue
            if not isinstance(content, dict):
                continue
            if content.get("ok") is True:
                try:
                    last = SearchVendorToolSuccess.model_validate(content)
                except Exception:
                    continue
            elif content.get("ok") is False:
                try:
                    last = SearchVendorToolError.model_validate(content)
                except Exception:
                    continue
    return last


def format_candidate_block(c: SearchVendorCandidate) -> str:
    """Single vendor: cosine score plus every populated field."""
    lines: list[str] = [f"**Confidence (cosine):** {c.score:.6f}"]
    field_order = [
        ("vendor_id", "Vendor ID"),
        ("legal_name", "Legal name"),
        ("secondary_name", "Secondary name"),
        ("company_code", "Company code"),
        ("address", "Address"),
        ("city", "City"),
        ("state", "State"),
        ("postal_code", "Postal code"),
        ("country", "Country"),
        ("vat_id", "VAT / tax ID"),
    ]
    for attr, label in field_order:
        val = getattr(c, attr, None)
        if val is not None and str(val).strip():
            lines.append(f"**{label}:** {val}")
    return "\n\n".join(lines)


def format_search_tool_markdown(success: SearchVendorToolSuccess) -> str:
    """Main chat body: threshold-qualified candidates only; vendor facts + scores only."""
    if not success.candidates:
        return (
            "_No vendor met the partial similarity threshold. "
            "See **Agent run details** for full top‑k retrieval scores._"
        )
    blocks: list[str] = []
    for i, c in enumerate(success.candidates, start=1):
        blocks.append(f"### {i}. {c.legal_name}\n\n{format_candidate_block(c)}")
    return "\n\n---\n\n".join(blocks)


def format_search_tool_error_markdown(err: SearchVendorToolError) -> str:
    return f"**Vendor search failed:** {err.message}"


def assistant_markdown_from_run(result: Any) -> str:
    """Map agent run result to main chat markdown (tool-first; LLM text fallback)."""
    tool_out = extract_search_vendors_tool_result(result)
    if isinstance(tool_out, SearchVendorToolSuccess):
        return format_search_tool_markdown(tool_out)
    if isinstance(tool_out, SearchVendorToolError):
        return format_search_tool_error_markdown(tool_out)
    out = getattr(result, "output", None)
    if isinstance(out, str) and out.strip():
        return out.strip()
    return "_No vendor search result in this turn._"
