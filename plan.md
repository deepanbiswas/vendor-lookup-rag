# Implementation plan: Vendor Lookup RAG

TDD-first delivery aligned with [specs/vendor-lookup-agent-specifications.md](specs/vendor-lookup-agent-specifications.md) and [docs/architecture.md](docs/architecture.md).

## Principles

- **Progressive infra:** Ollama on the host (Metal) for local dev; Qdrant via Docker Compose when indexing/searching; **vendor FastAPI** (`vendor-api`) serves the agent; **Streamlit** is an HTTP client only.
- **Tests:** Default `pytest` runs **unit tests** (no services). Markers: `integration`, `requires_ollama` for optional real-service checks.
- **Security baselines:** See [docs/security-notes.md](docs/security-notes.md) (pinned in `pyproject.toml`).

## Iterations (tracking)

| # | Iteration | Exit criteria | Done |
|---|-----------|---------------|------|
| 1 | Config + deps + pytest markers | `Settings` + `get_settings()`; unit tests; markers registered | [x] |
| 2 | Text normalization | `normalize_text()`; table-driven unit tests | [x] |
| 3 | Vendor models + CSV | `VendorRecord`, `load_vendor_csv()`; fixture CSV tests | [x] |
| 4 | Match classification | `classify_matches()` exact/partial/none; unit tests | [x] |
| 5 | Ollama embeddings | `OllamaEmbedder`; `respx` unit tests; optional `@requires_ollama` | [x] |
| 6 | Qdrant adapter + Compose | `VendorVectorStore`; `:memory:` tests; `docker-compose.yml` (Qdrant ≥ 1.16) | [x] |
| 7 | Ingestion + CLI | `ingest_vendor_csv`, `vendor-ingest` script; mocked test | [x] |
| 8 | Retrieval | `retrieve_vendors()`; unit tests with mocks | [x] |
| 9 | Pydantic AI agent | `build_vendor_agent()` + `search_vendors` tool | [x] |
| 10 | Streamlit + vendor REST API | `vendor_lookup_rag.api` (FastAPI); Streamlit calls `VENDOR_LOOKUP_API_BASE_URL`; `streamlit run …` | [x] |
| 11 | Compose + CI + runbook | `.env.example`, `api` + `app` services, [`.github/workflows/vendor-lookup-rag-ci.yml`](.github/workflows/vendor-lookup-rag-ci.yml), README | [x] |

## Commands (cheat sheet)

```bash
docker compose up -d          # Qdrant (+ api + app when using full compose)
cp .env.example .env            # adjust URLs/models
pip install -e ".[dev]"
pytest
vendor-ingest path/to/vendors.csv
vendor-api                    # REST API (default :8000); or: python -m vendor_lookup_rag.api
streamlit run frontend/streamlit/src/vendor_lookup_streamlit/app.py   # set VENDOR_LOOKUP_API_BASE_URL if not default
```

## CSV format

Required columns: `vendor_id`, `legal_name`. Optional: `city`, `postal_code` (or `zip`), `vat_id` (or `vat`), `country`.
