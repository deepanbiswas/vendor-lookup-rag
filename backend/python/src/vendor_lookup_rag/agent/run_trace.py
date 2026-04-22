"""Format pydantic-ai run results for display in the Streamlit UI (not OTLP export)."""

from __future__ import annotations

import json
from typing import Any


def format_agent_run_trace(result: Any) -> str:
    """
    Human-readable trace: run id, optional W3C traceparent, token usage, new messages JSON.

    OpenTelemetry spans are exported separately (Logfire/OTLP); this mirrors the agent transcript.
    """
    lines: list[str] = []
    run_id = getattr(result, "run_id", None)
    if run_id is not None:
        lines.append(f"run_id: {run_id}")

    tp = getattr(result, "_traceparent", None)
    if callable(tp):
        try:
            tval = tp(required=False)
            if tval:
                lines.append(f"traceparent: {tval}")
        except Exception:
            pass
    elif getattr(result, "_traceparent_value", None):
        lines.append(f"traceparent: {result._traceparent_value}")

    usage_fn = getattr(result, "usage", None)
    if callable(usage_fn):
        try:
            u = usage_fn()
            it = getattr(u, "input_tokens", 0)
            ot = getattr(u, "output_tokens", 0)
            tot = getattr(u, "total_tokens", it + ot)
            lines.append(f"usage: input_tokens={it} output_tokens={ot} total_tokens={tot}")
        except Exception:
            lines.append("usage: (unavailable)")

    nm = getattr(result, "new_messages_json", None)
    if callable(nm):
        try:
            raw = nm()
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            parsed = json.loads(raw) if raw else []
            lines.append("new_messages:")
            lines.append(json.dumps(parsed, indent=2, ensure_ascii=False))
        except Exception as e:
            lines.append(f"new_messages: (could not serialize: {e})")

    return "\n".join(lines) if lines else "(no trace data)"
