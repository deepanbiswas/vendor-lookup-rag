# Switching vector store, embeddings, and agent runtime

This project uses **hexagonal-style ports** under [`backend/python/src/vendor_lookup_rag/ports/`](../backend/python/src/vendor_lookup_rag/ports/). Domain code (`retrieval`, `agent/runner` tool body) depends only on those protocols. **Composition roots** construct concrete adapters:

| Role | Port | Default adapter | Typical composition sites |
|------|------|-----------------|---------------------------|
| Vector index | `VectorStore` | `QdrantVectorStore` | [`api/deps.py`](../backend/python/src/vendor_lookup_rag/api/deps.py) `build_production_runtime` (via `open_vector_store`), [`ingestion/pipeline.py`](../backend/python/src/vendor_lookup_rag/ingestion/pipeline.py) |
| Text embeddings | `TextEmbedder` | `OllamaEmbedder` | Same + `AgentDeps` |
| Chat agent | `VendorAgentRunner` | `PydanticAiVendorAgent` via `build_vendor_agent()` | [`api/deps.py`](../backend/python/src/vendor_lookup_rag/api/deps.py) `make_vendor_agent_runner`, re-exported from [`agent/__init__.py`](../backend/python/src/vendor_lookup_rag/agent/__init__.py) |

Unit tests use **port fakes** in [`tests/fakes/`](../backend/python/tests/fakes/) (`FakeVectorStore`, `FakeTextEmbedder`, `FakeVendorAgentRunner`).

---

## 1. Replace Qdrant with another vector database

1. Add a module under `backend/python/src/vendor_lookup_rag/adapters/<backend>/vector_store.py`.
2. Implement every method on [`VectorStore`](../backend/python/src/vendor_lookup_rag/ports/vector_store.py):

```python
# adapters/pgvector/store.py (illustrative skeleton)
from collections.abc import Sequence

from vendor_lookup_rag.models.records import SearchHit, VendorRecord


class PgVectorStore:
    def ensure_collection(self) -> None:
        ...

    def upsert_vendor(self, *, vendor_id: str, vector: list[float], record: VendorRecord) -> None:
        self.upsert_vendors_batch([(vendor_id, vector, record)])

    def upsert_vendors_batch(
        self,
        items: Sequence[tuple[str, list[float], VendorRecord]],
    ) -> None:
        ...

    def search(self, vector: list[float], limit: int) -> list[SearchHit]:
        ...
```

3. **Wire** the adapter where the app builds dependencies:
   - REST API: replace `QdrantVectorStore(...)` in `open_vector_store` (used by [`api/deps.py`](../backend/python/src/vendor_lookup_rag/api/deps.py) `build_production_runtime`) with your class (and connection params from `Settings`).
   - CLI ingest: pass `store=YourStore(...)` into `ingest_vendor_csv`, or change the default branch in [`ingestion/pipeline.py`](../backend/python/src/vendor_lookup_rag/ingestion/pipeline.py) when `store` is omitted.
4. Extend [`Settings`](../backend/python/src/vendor_lookup_rag/config/settings.py) with URLs, table/collection names, credentials, and optionally a `vector_backend: Literal["qdrant", "pgvector"]` to select an implementation in one factory function.

Cosine distance and vector dimension must stay consistent with `Settings.embedding_vector_size` and your embedding model.

---

## 2. Replace Ollama embeddings (OpenAI, Bedrock, …)

1. Implement [`TextEmbedder`](../backend/python/src/vendor_lookup_rag/ports/embedding.py) (`embed(text: str) -> list[float]`).

```python
# adapters/openai_embed/embedder.py (illustrative)
import httpx

from vendor_lookup_rag.config import Settings


class OpenAiTextEmbedder:
    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self._model = settings.embedding_model  # or a dedicated openai_embedding_model field
        self._key = settings.openai_api_key  # add to Settings
        self._client = client or httpx.Client(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {self._key}"},
            timeout=120.0,
        )

    def embed(self, text: str) -> list[float]:
        r = self._client.post("/embeddings", json={"model": self._model, "input": text})
        r.raise_for_status()
        data = r.json()
        return data["data"][0]["embedding"]
```

2. **Wire** instances into:
   - `AgentDeps(embedder=..., store=..., settings=...)`
   - `retrieve_vendors(..., embedder=...)`
   - `ingest_vendor_csv(..., embedder=...)` (optional `store=` for tests/custom backends).

3. If the embedder holds connections, implement `close()`; [`ingest_vendor_csv`](../backend/python/src/vendor_lookup_rag/ingestion/pipeline.py) calls `close()` when it created the embedder.

---

## 3. Replace Pydantic AI (LangGraph, direct OpenAI tools, …)

1. Implement [`VendorAgentRunner`](../backend/python/src/vendor_lookup_rag/ports/agent_runner.py) for your `AgentDeps` type: a `run_sync(user_message, *, deps=...)` method returning a result object the UI can use.

2. The **REST API** maps the run result with [`assistant_markdown_from_run`](../backend/python/src/vendor_lookup_rag/ui/chat_display.py) and [`format_agent_run_trace`](../backend/python/src/vendor_lookup_rag/agent/run_trace.py). Preserve:
   - `result.output` (final assistant string)
   - Optional: `run_id`, `usage()`, `new_messages_json()`, `_traceparent(...)` for traces. Either keep that shape or update those formatters and the API response fields.

```python
# adapters/langgraph_runner/runner.py (illustrative sketch)
from vendor_lookup_rag.agent.deps import AgentDeps
from vendor_lookup_rag.ports.agent_runner import VendorAgentRunner


class LangGraphVendorRunner:
    def run_sync(self, user_message: str, *, deps: AgentDeps) -> MyRunResult:
        # Build graph with tools that call search_vendors_tool_body(deps, query)
        ...
        return MyRunResult(output=text, ...)
```

3. Export a `build_vendor_agent(settings) -> VendorAgentRunner` (or rename) from [`agent/__init__.py`](../backend/python/src/vendor_lookup_rag/agent/__init__.py) and wire it through `make_vendor_agent_runner` in [`adapters/factory.py`](../backend/python/src/vendor_lookup_rag/adapters/factory.py) so the **API** process picks it up.

4. **Observability:** [`logfire.instrument_pydantic_ai()`](../backend/python/src/vendor_lookup_rag/observability/logfire.py) applies only to Pydantic AI; other frameworks need their own instrumentation.

---

## 4. Settings and factories (implemented)

[`Settings`](../backend/python/src/vendor_lookup_rag/config/settings.py) includes **backend discriminators** (single option each today; extend the `Literal` when you add another implementation):

| Field | Env alias | Values |
|-------|-----------|--------|
| `vector_backend` | `VENDOR_LOOKUP_VECTOR_BACKEND` | `qdrant` |
| `embedding_backend` | `VENDOR_LOOKUP_EMBEDDING_BACKEND` | `ollama` |
| `agent_backend` | `VENDOR_LOOKUP_AGENT_BACKEND` | `pydantic_ai` |

Central wiring lives in [`adapters/factory.py`](../backend/python/src/vendor_lookup_rag/adapters/factory.py):

- **`open_vector_store(settings, *, client=None, check_compatibility=True) -> VectorStoreHandle`** — returns `store`, `qdrant_client`, and `own_client` for correct `close()` behavior in ingest. Used by [`api/deps.py`](../backend/python/src/vendor_lookup_rag/api/deps.py) `build_production_runtime` (with `check_compatibility=False`) and by [`ingest_vendor_csv`](../backend/python/src/vendor_lookup_rag/ingestion/pipeline.py) when no custom `store` is injected.
- **`make_text_embedder(settings) -> TextEmbedder`** — used by the API runtime and ingest when no custom embedder is passed.
- **`make_vendor_agent_runner(settings) -> PydanticAiVendorAgent`** — used by the API instead of calling `build_vendor_agent` directly.

**Adding another backend** (e.g. pgvector, OpenAI embeddings, LangGraph):

1. Extend the corresponding `Literal[...]` on `Settings` with the new name.
2. Add env-backed URLs/secrets as needed.
3. Branch inside the matching factory function and return an object that implements the port (`VectorStore`, `TextEmbedder`, or `VendorAgentRunner`).
4. Keep validation in `Settings`; avoid introducing a second config abstraction unless you must (see section 5).

---

## 5. Should `Settings` and Pydantic models be abstracted?

**Recommendation for this codebase: do not abstract Pydantic / pydantic-settings for configuration or domain DTOs by default.**

**Why infrastructure ports are enough**

- Swapping Qdrant, Ollama, or Pydantic AI does **not** require removing `BaseSettings` or `Field`. Those adapters read simple types (`str`, `int`, URLs) from settings.
- Domain records ([`VendorRecord`](../backend/python/src/vendor_lookup_rag/models/records.py), tool result models) use Pydantic for validation and JSON compatibility with Qdrant payloads and tool schemas. Replacing that layer means rewriting validation and serialization across retrieval, ingestion, and the agent.

**When abstracting configuration might make sense**

- Multiple incompatible config backends (Vault-only, legacy INI, etc.) must be hidden behind one interface.
- You publish a **library** that must not depend on pydantic-settings.

**Costs of abstracting `Settings`**

- Duplicated validation logic and worse IDE/autocomplete for env vars.
- Every new setting touches both an interface and an implementation.
- More test doubles without a clear second implementation.

**Pragmatic rule**

| Couple to a port | Usually leave as-is |
|------------------|---------------------|
| Vector index, embedder, agent runner, HTTP “service” clients | `Settings` / env loading, logging, stdlib, Pydantic DTOs for stable JSON/schema |

**Pydantic AI vs Pydantic (models)**

- **Pydantic AI** is an orchestration/runtime dependency → already behind `VendorAgentRunner` + `adapters/pydantic_ai/`.
- **Pydantic `BaseModel`** for data shapes is a **schema tool**, not a swappable runtime service in the same sense; abstracting it is rarely worth the churn unless you are migrating the entire stack off Pydantic.

---

## Application logging (stdout + optional file)

Structured logs use the `vendor_lookup_rag` logger family. Call [`configure_app_logging`](../backend/python/src/vendor_lookup_rag/observability/app_logging.py) once at process entry (Streamlit `main`, FastAPI lifespan / `vendor-api`, `vendor-ingest` CLI).

- **`VENDOR_LOOKUP_LOG_LEVEL`**: `ERROR` (default), `WARNING`, `INFO`, `DEBUG` (`WARN` is accepted as `WARNING`). Applies to **both** stdout and file handlers.
- **`VENDOR_LOOKUP_LOG_DIR`**: If set, writes a rotating `vendor_lookup_rag.log` under that directory; stdout logging is always enabled.

This is separate from JSON-line **telemetry** (`VENDOR_LOOKUP_TELEMETRY_LOG_DIR`, etc.).

---

## C# backend (same idea)

The C# API in [`backend/csharp/`](../backend/csharp/) mirrors the same **ports and adapters** shape: `ITextEmbedder`, `IVectorStore` (Qdrant via gRPC, [`Qdrant.Client`](https://github.com/qdrant/qdrant-dotnet)), with `Adapters/Qdrant/IQdrantPointSearch` (implemented by `QdrantClientPointSearch`) sitting between the vector store and the gRPC client so the mapping and search call path are testable without a live Qdrant; and the chat agent (`Agents/VendorLookupAgent`). New implementations are wired in `Composition/ServiceCollectionExtensions` (`AddVendorLookupRagCore`). See [`backend/csharp/README.md`](../backend/csharp/README.md) for build, test, and run instructions.

---

## Related code

- Python ports: [`backend/python/src/vendor_lookup_rag/ports/`](../backend/python/src/vendor_lookup_rag/ports/)
- Python adapters: [`backend/python/src/vendor_lookup_rag/adapters/`](../backend/python/src/vendor_lookup_rag/adapters/)
- Python factories: [`backend/python/src/vendor_lookup_rag/adapters/factory.py`](../backend/python/src/vendor_lookup_rag/adapters/factory.py)
- App logging: [`backend/python/src/vendor_lookup_rag/observability/app_logging.py`](../backend/python/src/vendor_lookup_rag/observability/app_logging.py)
- Test fakes: [`tests/fakes/`](../backend/python/tests/fakes/)
- C# ports and composition: [`backend/csharp/src/VendorLookupRag/`](../backend/csharp/src/VendorLookupRag/) (see `Composition/`, `Ports/`, `Adapters/`, `Agents/`)
