"""Optional Logfire wiring; OTEL spans come from :class:`pydantic_ai.Agent` ``instrument=``."""

from __future__ import annotations

import logging

from vendor_lookup_rag.config import Settings

logger = logging.getLogger(__name__)

_configured_logfire = False


def configure_observability(settings: Settings) -> None:
    """
    When ``VENDOR_LOOKUP_LOGFIRE`` is set, configure Logfire and patch Pydantic AI.

    Requires the optional ``logfire`` package (``pip install 'vendor-lookup-rag[observability]'``).
    OpenTelemetry export for LLM/tool spans uses env vars (e.g. ``OTEL_EXPORTER_OTLP_ENDPOINT``)
    when :attr:`Settings.agent_instrument` is true on the agent.
    """
    global _configured_logfire
    if not settings.logfire_enabled:
        return
    if _configured_logfire:
        return
    try:
        import logfire
    except ImportError:
        logger.warning(
            "VENDOR_LOOKUP_LOGFIRE is set but logfire is not installed. "
            "Install optional extras: pip install 'vendor-lookup-rag[observability]'"
        )
        return
    kwargs: dict = {}
    if settings.logfire_service_name:
        kwargs["service_name"] = settings.logfire_service_name
    logfire.configure(**kwargs)
    logfire.instrument_pydantic_ai()
    _configured_logfire = True
