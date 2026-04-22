"""Streamlit chat UI for vendor lookup (REST client to the vendor API)."""

from __future__ import annotations

import hashlib
import json
import logging

import httpx
import streamlit as st

from vendor_lookup_streamlit.api_client import fetch_status, post_chat
from vendor_lookup_streamlit.settings import StreamlitSettings, get_settings

# Cap session history to avoid unbounded memory on long sessions.
MAX_CHAT_MESSAGES = 128

_logger = logging.getLogger(__name__)


def _settings_cache_signature(s: StreamlitSettings) -> str:
    """Stable hash so ``st.cache_data`` rebuilds when ``.env`` / env vars change."""
    payload = json.dumps(
        {
            "vendor_lookup_api_base_url": s.vendor_lookup_api_base_url,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


@st.cache_data(ttl=15)
def _cached_api_status(settings_sig: str, api_base_url: str) -> dict | None:
    """Sidebar status from API; ``None`` if unreachable."""
    try:
        return fetch_status(api_base_url)
    except Exception as e:
        _logger.warning("API status check failed: %s", e)
        return None


def _trim_messages(messages: list[dict]) -> None:
    while len(messages) > MAX_CHAT_MESSAGES:
        messages.pop(0)


def _format_agent_trace(trace: str) -> str:
    """Keep assistant lines readable and pretty-print the trailing ``last_tool_result`` JSON (often one long line from the API)."""
    if not trace or not trace.strip():
        return trace
    marker = "last_tool_result: "
    idx = trace.find(marker)
    if idx < 0:
        return trace
    prefix = trace[: idx + len(marker)]
    rest = trace[idx + len(marker) :].lstrip()
    if not rest:
        return prefix
    try:
        parsed = json.loads(rest)
        body = json.dumps(parsed, indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError, ValueError):
        body = rest
    return f"{prefix.rstrip()}\n{body}"


def main() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO)
    get_settings.cache_clear()
    s_boot = get_settings()
    st.set_page_config(page_title="Vendor Lookup", page_icon="🔎")
    st.title("Vendor Lookup Agent")
    st.caption("Local RAG against your vendor master (Ollama + Qdrant via API).")

    sig = _settings_cache_signature(s_boot)
    api_base = s_boot.vendor_lookup_api_base_url
    status = _cached_api_status(sig, api_base)
    s = s_boot

    if "messages" not in st.session_state:
        st.session_state.messages = []

    pending = st.session_state.get("pending_agent_prompt")
    agent_busy = pending is not None
    show_trace = bool(st.session_state.get("show_agent_trace", False))

    with st.sidebar:
        st.subheader("Connection")
        if status is None:
            st.markdown(f"🔴 **API:** `{api_base}` unreachable")
        else:
            st.markdown(f"🟢 **API:** `{api_base}`")
            for name, svc in status.get("services", {}).items():
                ok = svc.get("ok", False)
                detail = svc.get("detail", "")
                icon = "🟢" if ok else "🔴"
                st.markdown(f"{icon} **{name}:** `{detail}`")
        st.caption("Checks refresh every ~15s (cached).")

        st.subheader("Models")
        if status is not None:
            st.code(
                f"chat: {status.get('chat_model', '')}\nembed: {status.get('embedding_model', '')}",
                language="text",
            )
            st.caption(
                f"Match thresholds (from API): exact ≥ {status.get('score_threshold_exact', '')}, "
                f"partial ≥ {status.get('score_threshold_partial', '')}, "
                f"tolerance ±{status.get('score_tolerance', '')}"
            )
        else:
            st.caption("Start the API server to load model names from `/v1/status`.")

        st.subheader("Observability")
        st.caption(
            "OpenTelemetry / Logfire traces are exported from the **API** process to your configured backends "
            "(not rendered here). The toggle below shows the **agent run transcript** "
            "(full top‑k retrieval, usage, messages) under replies."
        )
        st.checkbox(
            "Show agent run details under replies",
            key="show_agent_trace",
            disabled=agent_busy,
            help="Hidden while a search is running so toggling does not interrupt the run.",
        )

        if st.button("Clear chat", type="secondary"):
            st.session_state.messages = []
            st.session_state.pop("pending_agent_prompt", None)
            st.rerun()

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if (
                show_trace
                and m["role"] == "assistant"
                and m.get("trace")
            ):
                with st.expander("Agent run details (transcript & usage)", expanded=False):
                    st.code(
                        _format_agent_trace(m["trace"]),
                        language="text",
                        line_numbers=True,
                    )

    if pending is not None:
        with st.spinner("Thinking…"):
            try:
                display, trace_text = post_chat(api_base, pending)
                _logger.info("Chat turn completed (display length=%s chars).", len(display))
            except httpx.HTTPStatusError as e:
                code = e.response.status_code
                detail = ""
                try:
                    j = e.response.json()
                    detail = (
                        (j.get("detail") or j.get("message") or "")
                        or str(j)
                    )
                except Exception:
                    detail = (e.response.text or str(e))[:10000]
                st.error(
                    f"**HTTP {code}** when calling the vendor API (`POST /v1/chat`). "
                    f"Health may still be OK; this is usually a failure during the Ollama agent turn or Qdrant retrieval. "
                    f"**API base:** `{api_base}`. On Docker, check `docker logs` on the C# API container. "
                    f"\n\n**Response detail:**\n\n`{detail}`"
                )
                st.session_state.pop("pending_agent_prompt", None)
                st.stop()
            except Exception as e:
                st.error(
                    "**Something went wrong calling the vendor API.** "
                    f"Check that the server is running at `{api_base}`.\n\n`{e}`"
                )
                st.session_state.pop("pending_agent_prompt", None)
                st.stop()
        st.session_state.messages.append(
            {"role": "assistant", "content": display, "trace": trace_text},
        )
        _trim_messages(st.session_state.messages)
        st.session_state.pop("pending_agent_prompt", None)
        st.rerun()

    if prompt := st.chat_input("Describe the vendor (name, VAT, city, …)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        _trim_messages(st.session_state.messages)
        st.session_state.pending_agent_prompt = prompt
        st.rerun()


if __name__ == "__main__":
    main()
