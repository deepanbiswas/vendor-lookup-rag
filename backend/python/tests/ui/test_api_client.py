"""Tests that the Streamlit HTTP client calls the vendor API over httpx."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from vendor_lookup_streamlit.api_client import fetch_status, post_chat


def test_fetch_status_uses_httpx_get_to_v1_status() -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "services": {"ollama": {"ok": True, "detail": "reachable"}},
        "chat_model": "m",
        "embedding_model": "e",
        "score_threshold_exact": 0.9,
        "score_threshold_partial": 0.5,
        "score_tolerance": 0.0,
    }
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("vendor_lookup_streamlit.api_client.httpx.Client", return_value=mock_client):
        out = fetch_status("http://127.0.0.1:8000")

    mock_client.get.assert_called_once()
    assert "/v1/status" in mock_client.get.call_args[0][0]
    assert out["chat_model"] == "m"


def test_post_chat_uses_httpx_post_to_v1_chat() -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"display_markdown": "# x", "trace_text": "t"}
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("vendor_lookup_streamlit.api_client.httpx.Client", return_value=mock_client):
        dm, tt = post_chat("http://api:8000", "hello")

    mock_client.post.assert_called_once()
    assert "/v1/chat" in mock_client.post.call_args[0][0]
    assert mock_client.post.call_args[1]["json"] == {"message": "hello"}
    assert dm == "# x"
    assert tt == "t"
