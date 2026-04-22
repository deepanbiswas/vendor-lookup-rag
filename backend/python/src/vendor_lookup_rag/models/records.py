"""Domain models for vendor records and retrieval."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class VendorRecord(BaseModel):
    """One row from the vendor master CSV after validation."""

    vendor_id: str = Field(..., description="Stable identifier for the vendor row.")
    legal_name: str = Field(..., min_length=1)
    city: str | None = None
    postal_code: str | None = None
    vat_id: str | None = None
    country: str | None = None
    secondary_name: str | None = None
    company_code: str | None = None
    address: str | None = None
    state: str | None = None
    date_format: str | None = None
    eu_member_flag: str | None = None
    extras: dict[str, str] = Field(
        default_factory=dict,
        description="CSV columns not mapped to a logical field (stable Qdrant payload).",
    )

    @field_validator("vendor_id", "legal_name", mode="before")
    @classmethod
    def strip_required_strings(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator(
        "city",
        "postal_code",
        "vat_id",
        "country",
        "secondary_name",
        "company_code",
        "address",
        "state",
        "date_format",
        "eu_member_flag",
        mode="before",
    )
    @classmethod
    def strip_optional_strings(cls, v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, str):
            s = v.strip()
            return s if s else None
        return v

    @field_validator("extras", mode="before")
    @classmethod
    def normalize_extras(cls, v: Any) -> dict[str, str]:
        if not v:
            return {}
        if not isinstance(v, dict):
            raise TypeError("extras must be a dict")
        out: dict[str, str] = {}
        for k, val in v.items():
            kk = str(k).strip().lower()
            if not kk:
                continue
            if isinstance(val, str) and (vv := val.strip()):
                out[kk] = vv
        return out

    def embedding_text(self) -> str:
        """Concatenate fields for embedding (normalized separately by caller if needed)."""
        parts = [
            self.legal_name,
            self.secondary_name or "",
            self.company_code or "",
            self.address or "",
            self.city or "",
            self.state or "",
            self.postal_code or "",
            self.vat_id or "",
            self.country or "",
        ]
        base = " ".join(p for p in parts if p)
        if self.extras:
            extra_bits = " ".join(self.extras[k] for k in sorted(self.extras))
            if base:
                return f"{base} {extra_bits}"
            return extra_bits
        return base


class SearchHit(BaseModel):
    """One Qdrant hit with score."""

    score: float
    record: VendorRecord


class SearchVendorCandidate(BaseModel):
    """One row returned to the chat model from ``search_vendors``."""

    score: float
    vendor_id: str
    legal_name: str
    secondary_name: str | None = None
    company_code: str | None = None
    city: str | None = None
    vat_id: str | None = None
    address: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None


class SearchVendorToolSuccess(BaseModel):
    """Successful vendor search tool result (structured schema for the LLM)."""

    ok: Literal[True] = True
    kind: str
    message: str
    candidates: list[SearchVendorCandidate]
    retrieval_top_k: list[SearchVendorCandidate] = Field(
        default_factory=list,
        description="All vector hits before partial-threshold filtering (diagnostics / agent trace).",
    )


class SearchVendorToolError(BaseModel):
    """Structured error when retrieval or embedding fails (e.g. Ollama/Qdrant down)."""

    ok: Literal[False] = False
    error: str
    message: str
    detail: str | None = None


SearchVendorToolResult = SearchVendorToolSuccess | SearchVendorToolError
