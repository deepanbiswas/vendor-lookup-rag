"""Pydantic AI implementation of :class:`~vendor_lookup_rag.ports.agent_runner.VendorAgentRunner`."""

from __future__ import annotations

import logging
from typing import Any

from pydantic_ai import Agent, RunContext

_logger = logging.getLogger(__name__)
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

from vendor_lookup_rag.agent.deps import AgentDeps
from vendor_lookup_rag.agent.runner import SYSTEM_PROMPT, search_vendors_tool_body
from vendor_lookup_rag.config import Settings, get_settings
from vendor_lookup_rag.models import SearchVendorToolResult


def build_vendor_agent(settings: Settings | None = None) -> "PydanticAiVendorAgent":
    """Create an agent wired to Ollama chat and the retrieval tool."""
    s = settings or get_settings()
    provider = OllamaProvider(base_url=s.ollama_openai_api_base())
    model = OpenAIChatModel(s.chat_model, provider=provider)
    instrument = s.agent_instrument
    agent: Agent[AgentDeps, str] = Agent(
        model,
        deps_type=AgentDeps,
        system_prompt=SYSTEM_PROMPT,
        instrument=instrument,
    )

    @agent.tool
    async def search_vendors(ctx: RunContext[AgentDeps], user_query: str) -> SearchVendorToolResult:
        return search_vendors_tool_body(ctx.deps, user_query)

    return PydanticAiVendorAgent(agent)


class PydanticAiVendorAgent:
    """Thin wrapper so call sites depend on the port, not ``pydantic_ai.Agent``."""

    def __init__(self, agent: Agent[AgentDeps, str]) -> None:
        self._agent = agent

    @property
    def pydantic_agent(self) -> Agent[AgentDeps, str]:
        """Underlying Pydantic AI agent (for tests and instrumentation)."""
        return self._agent

    def run_sync(self, user_message: str, *, deps: AgentDeps) -> Any:
        try:
            return self._agent.run_sync(user_message, deps=deps)
        except Exception as e:
            _logger.exception("Pydantic AI agent run_sync failed: %s", e)
            raise
