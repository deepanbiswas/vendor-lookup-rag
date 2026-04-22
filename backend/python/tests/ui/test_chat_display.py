"""Tests for Streamlit chat markdown + tool JSON extraction."""

from __future__ import annotations

import json

from vendor_lookup_rag.models import SearchVendorCandidate, SearchVendorToolError, SearchVendorToolSuccess
from vendor_lookup_rag.ui.chat_display import (
    assistant_markdown_from_run,
    extract_search_vendors_tool_result,
    format_search_tool_error_markdown,
    format_search_tool_markdown,
)


def test_format_search_tool_markdown_lists_scores_and_fields() -> None:
    s = SearchVendorToolSuccess(
        kind="partial",
        message="ignored for main body",
        candidates=[
            SearchVendorCandidate(
                score=0.712,
                vendor_id="1",
                legal_name="ACME",
                city="Berlin",
                postal_code="10115",
                vat_id="DE1",
            )
        ],
        retrieval_top_k=[],
    )
    md = format_search_tool_markdown(s)
    assert "0.712000" in md or "0.712" in md
    assert "ACME" in md
    assert "Berlin" in md
    assert "10115" in md
    assert "DE1" in md


def test_extract_search_vendors_from_new_messages_json() -> None:
    payload = SearchVendorToolSuccess(
        kind="partial",
        message="m",
        candidates=[
            SearchVendorCandidate(
                score=0.8,
                vendor_id="v",
                legal_name="L",
                city="C",
            )
        ],
        retrieval_top_k=[
            SearchVendorCandidate(score=0.5, vendor_id="x", legal_name="Low", city=None),
        ],
    )

    class R:
        def new_messages_json(self) -> bytes:
            msg = {
                "parts": [
                    {
                        "part_kind": "tool-return",
                        "tool_name": "search_vendors",
                        "content": payload.model_dump(),
                    }
                ]
            }
            return json.dumps([msg]).encode("utf-8")

    got = extract_search_vendors_tool_result(R())
    assert isinstance(got, SearchVendorToolSuccess)
    assert got.retrieval_top_k[0].legal_name == "Low"


def test_format_search_tool_markdown_empty_candidates_shows_threshold_hint() -> None:
    s = SearchVendorToolSuccess(
        kind="none",
        message="none",
        candidates=[],
        retrieval_top_k=[
            SearchVendorCandidate(score=0.4, vendor_id="z", legal_name="Zed", city=None),
        ],
    )
    md = format_search_tool_markdown(s)
    assert "partial similarity threshold" in md
    assert "Agent run details" in md


def test_format_search_tool_error_markdown() -> None:
    e = SearchVendorToolError(error="retrieval_failed", message="Qdrant down", detail=None)
    assert "Qdrant down" in format_search_tool_error_markdown(e)
    assert "Vendor search failed" in format_search_tool_error_markdown(e)


def test_extract_tool_return_with_json_string_content() -> None:
    payload = SearchVendorToolSuccess(
        kind="partial",
        message="m",
        candidates=[SearchVendorCandidate(score=0.9, vendor_id="a", legal_name="A", city=None)],
        retrieval_top_k=[],
    )

    class R:
        def new_messages_json(self) -> bytes:
            msg = {
                "parts": [
                    {
                        "part_kind": "tool-return",
                        "tool_name": "search_vendors",
                        "content": json.dumps(payload.model_dump()),
                    }
                ]
            }
            return json.dumps([msg]).encode("utf-8")

    got = extract_search_vendors_tool_result(R())
    assert isinstance(got, SearchVendorToolSuccess)
    assert got.candidates[0].legal_name == "A"


def test_extract_last_tool_return_is_search_vendors_error() -> None:
    err = SearchVendorToolError(error="retrieval_failed", message="boom", detail=None)

    class R:
        def new_messages_json(self) -> bytes:
            msg = {
                "parts": [
                    {
                        "part_kind": "tool-return",
                        "tool_name": "search_vendors",
                        "content": err.model_dump(),
                    }
                ]
            }
            return json.dumps([msg]).encode("utf-8")

    got = extract_search_vendors_tool_result(R())
    assert isinstance(got, SearchVendorToolError)
    assert got.message == "boom"


def test_extract_returns_none_without_tool() -> None:
    class R:
        def new_messages_json(self) -> bytes:
            return json.dumps(
                [{"parts": [{"part_kind": "text", "content": "hello"}]}],
            ).encode("utf-8")

    assert extract_search_vendors_tool_result(R()) is None


def test_extract_returns_none_on_invalid_json() -> None:
    class R:
        def new_messages_json(self) -> bytes:
            return b"not-json"

    assert extract_search_vendors_tool_result(R()) is None


def test_extract_returns_none_when_new_messages_missing() -> None:
    assert extract_search_vendors_tool_result(object()) is None


def test_assistant_markdown_prefers_tool_success_over_llm_output() -> None:
    tool = SearchVendorToolSuccess(
        kind="partial",
        message="msg",
        candidates=[SearchVendorCandidate(score=0.8, vendor_id="1", legal_name="CO", city="X")],
        retrieval_top_k=[],
    )

    class R:
        output = "I will list many friendly words"

        def new_messages_json(self) -> bytes:
            msg = {
                "parts": [
                    {
                        "part_kind": "tool-return",
                        "tool_name": "search_vendors",
                        "content": tool.model_dump(),
                    }
                ]
            }
            return json.dumps([msg]).encode("utf-8")

    md = assistant_markdown_from_run(R())
    assert "CO" in md
    assert "friendly words" not in md


def test_assistant_markdown_fallback_to_model_output_when_no_tool() -> None:
    class R:
        output = "OK"

    assert assistant_markdown_from_run(R()) == "OK"


def test_assistant_markdown_fallback_when_empty_output() -> None:
    class R:
        output = ""

    assert "No vendor search result" in assistant_markdown_from_run(R())

