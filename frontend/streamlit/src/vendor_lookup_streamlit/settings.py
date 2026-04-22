"""Minimal settings for the Streamlit process (API base URL only by default)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class StreamlitSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    vendor_lookup_api_base_url: str = Field(
        default="http://127.0.0.1:8000",
        alias="VENDOR_LOOKUP_API_BASE_URL",
    )

    @field_validator("vendor_lookup_api_base_url", mode="before")
    @classmethod
    def strip_trailing_slash(cls, v: object) -> object:
        if isinstance(v, str):
            return v.rstrip("/")
        return v


@lru_cache
def get_settings() -> StreamlitSettings:
    return StreamlitSettings()
