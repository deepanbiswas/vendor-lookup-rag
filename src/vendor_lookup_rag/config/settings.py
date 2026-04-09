"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from vendor_lookup_rag.csv.mapping import (
    DEFAULT_COLUMN_MAPPING,
    ColumnMapping,
    load_column_mapping_from_json,
)


class Settings(BaseSettings):
    """Runtime configuration for Ollama, Qdrant, and matching thresholds."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for the Ollama HTTP API.",
    )
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="Qdrant HTTP API URL.",
    )
    qdrant_collection: str = Field(
        default="vendor_master",
        description="Qdrant collection name for vendor vectors.",
    )
    vector_backend: Literal["qdrant"] = Field(
        default="qdrant",
        description="Vector index implementation (extend when adding adapters).",
        alias="VENDOR_LOOKUP_VECTOR_BACKEND",
    )
    embedding_backend: Literal["ollama"] = Field(
        default="ollama",
        description="Text embedding provider (extend when adding OpenAI, Bedrock, …).",
        alias="VENDOR_LOOKUP_EMBEDDING_BACKEND",
    )
    agent_backend: Literal["pydantic_ai"] = Field(
        default="pydantic_ai",
        description="Agent orchestration implementation (extend when adding LangGraph, …).",
        alias="VENDOR_LOOKUP_AGENT_BACKEND",
    )
    embedding_model: str = Field(
        default="nomic-embed-text",
        description="Ollama embedding model name.",
    )
    chat_model: str = Field(
        default="gemma4:e4b",
        description="Ollama chat model tag for the agent (default: Gemma 4 E4B; e.g. gemma4:26b for 26B MoE).",
    )
    embedding_vector_size: int = Field(
        default=768,
        ge=1,
        description="Vector dimension (must match embedding model output).",
    )
    retrieval_top_k: int = Field(default=5, ge=1, le=100)
    score_threshold_exact: float = Field(
        default=0.92,
        ge=0.0,
        le=1.0,
        description="Cosine similarity at or above this suggests an exact match.",
    )
    score_threshold_partial: float = Field(
        default=0.55,
        ge=0.0,
        le=1.0,
        description="Minimum top score for a partial match.",
    )
    vendor_csv_column_map_path: str | None = Field(
        default=None,
        description="Optional JSON file merging logical field → header lists (see README).",
        alias="VENDOR_CSV_COLUMN_MAP_PATH",
    )
    ingest_upsert_batch_size: int = Field(
        default=128,
        ge=1,
        description="Max points per Qdrant upsert during CSV ingest.",
        alias="INGEST_UPSERT_BATCH_SIZE",
    )
    retrieval_min_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="If set, drop Qdrant hits below this cosine score before returning.",
        alias="RETRIEVAL_MIN_SCORE",
    )
    telemetry_log_dir: str | None = Field(
        default=None,
        description="Directory for vendor_retrieval.jsonl (JSON lines).",
        alias="VENDOR_LOOKUP_TELEMETRY_LOG_DIR",
    )
    telemetry_log_to_stderr: bool = Field(
        default=False,
        description="Emit retrieval telemetry JSON lines to stderr.",
        alias="TELEMETRY_LOG_TO_STDERR",
    )
    telemetry_log_to_stdout: bool = Field(
        default=False,
        description="Emit retrieval telemetry JSON lines to stdout.",
        alias="TELEMETRY_LOG_TO_STDOUT",
    )
    agent_instrument: bool = Field(
        default=True,
        description="Enable OpenTelemetry spans for Pydantic AI (model + tool calls).",
        alias="VENDOR_LOOKUP_AGENT_INSTRUMENT",
    )
    logfire_enabled: bool = Field(
        default=False,
        description="If true, call logfire.configure() and instrument_pydantic_ai() when logfire is installed.",
        alias="VENDOR_LOOKUP_LOGFIRE",
    )
    logfire_service_name: str | None = Field(
        default=None,
        description="Optional service name passed to logfire.configure(service_name=...).",
        alias="VENDOR_LOOKUP_LOGFIRE_SERVICE_NAME",
    )
    app_log_dir: str | None = Field(
        default=None,
        description="Directory for application log file vendor_lookup_rag.log (rotating). Stdout logging is always enabled.",
        alias="VENDOR_LOOKUP_LOG_DIR",
    )
    app_log_level: Literal["ERROR", "WARNING", "INFO", "DEBUG"] = Field(
        default="ERROR",
        description="Minimum level for stdout and file handlers (ERROR, WARNING, INFO, DEBUG; env may use WARN).",
        alias="VENDOR_LOOKUP_LOG_LEVEL",
    )

    @field_validator("app_log_level", mode="before")
    @classmethod
    def normalize_app_log_level(cls, v: object) -> object:
        if isinstance(v, str) and v.strip().upper() == "WARN":
            return "WARNING"
        return v

    @field_validator("ollama_base_url", "qdrant_url")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")

    def ollama_openai_api_base(self) -> str:
        """OpenAI-compatible base URL for pydantic-ai Ollama provider (…/v1)."""
        u = self.ollama_base_url
        if u.endswith("/v1"):
            return u
        return f"{u}/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_column_mapping(settings: Settings | None = None) -> ColumnMapping:
    """Default mapping, or JSON at ``VENDOR_CSV_COLUMN_MAP_PATH`` merged onto defaults."""
    s = settings or get_settings()
    p = s.vendor_csv_column_map_path
    if p:
        return load_column_mapping_from_json(Path(p))
    return DEFAULT_COLUMN_MAPPING
