# Vendor Lookup RAG (local)

Vendor lookup on a vendor master list using **RAG**, **Ollama** (embeddings + chat), **Qdrant**, and **Pydantic AI**, with **TDD** and **spec-driven development**.

This is a **standalone** Git repository (clone it on its own; it is no longer under `vendor_lookup`).

## Layout


| Path                     | Purpose                                                                |
| ------------------------ | ---------------------------------------------------------------------- |
| `src/vendor_lookup_rag/` | Application package (subpackages by concern; see below)                |
| `tests/`                 | Pytest, grouped by area (`config/`, `csv/`, `agent/`, `ingestion/`, …) |
| `specs/`                 | Specs and `@pytest.mark.spec(...)` links                               |
| `docs/`                  | Architecture, adapter switching, security notes                        |
| `plan.md`                | Implementation iterations (tracking)                                   |


**Source subpackages (aligned with implementation iterations):** `config/` (settings), `models/` (domain + tool payloads), `csv/` (mapping + loader), `normalization/`, `matching/`, `embedding/` (Ollama), `vector/` (Qdrant store), `retrieval/`, `telemetry/`, `ingestion/` (pipeline + CLI), `agent/` (Pydantic AI), `api/` (FastAPI REST layer), `observability/`, `health/`, `ui/` (Streamlit client). The top-level `app.py` re-exports the UI entry for `streamlit run src/vendor_lookup_rag/app.py`.

## Quick start (development)

```bash
cd vendor-lookup-rag   # or your clone directory
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## Local stack

**Docker deployment (Qdrant + vendor API + Streamlit in containers, Ollama on the host via `scripts/`):** see [`deploy-and-run.md`](deploy-and-run.md).

1. **Ollama** (host install, [ollama.com](https://ollama.com)) — recommended on Apple Silicon for Metal. Pull models, e.g. `ollama pull nomic-embed-text` and `ollama pull gemma4:e4b` (or `gemma4:26b` if you switch `CHAT_MODEL` in `.env`; tags must match `ollama list`).
2. **Qdrant** — `docker compose up -d` in this directory (see `docker-compose.yml`, image `≥ 1.16.0`).
3. **Environment** — `cp .env.example .env` and adjust URLs/models.

Default URLs: Ollama `http://localhost:11434`, Qdrant `http://localhost:6333`, vendor API `http://127.0.0.1:8000` (Streamlit uses `VENDOR_LOOKUP_API_BASE_URL` to reach it).

### Health checks and integration test env

Before integration tests or heavy jobs, verify Qdrant and (if needed) Ollama with the same endpoints as [`src/vendor_lookup_rag/health/http.py`](src/vendor_lookup_rag/health/http.py) (Qdrant `GET …/readyz`, Ollama `GET …/api/tags`). To also confirm the **vendor HTTP API** is up (after starting `vendor-api`), use **`with-api`**:

```bash
./scripts/verify_stack.sh
./scripts/verify_stack.sh qdrant-only   # same surface as the CI Qdrant integration job
./scripts/verify_stack.sh with-api      # Qdrant + Ollama + GET …/v1/health (optional; needs vendor-api running)
# Override API URL: VENDOR_LOOKUP_API_BASE_URL=http://localhost:8000 ./scripts/verify_stack.sh with-api
```

Use the same variable names **locally and in CI** for pytest. `tests/conftest.py` defaults match `.env.example` when variables are unset.

| Variable | Role | Typical local | CI (Qdrant integration job) |
|----------|------|---------------|----------------------------|
| `QDRANT_URL` | Qdrant HTTP API (ingest, retrieval, **API** process) | `http://localhost:6333` | `http://127.0.0.1:6333` |
| `OLLAMA_BASE_URL` | Ollama HTTP API (**API** process and CLI ingest) | `http://localhost:11434` | *(not set in Qdrant-only job)* |
| `VENDOR_LOOKUP_API_BASE_URL` | Vendor REST API (**Streamlit** only) | `http://127.0.0.1:8000` | *(N/A in default CI; UI not exercised)* |

**Integration (Qdrant, no live Ollama)** — align with `.github/workflows/vendor-lookup-rag-ci.yml`:

```bash
export QDRANT_URL="${QDRANT_URL:-http://127.0.0.1:6333}"
./scripts/verify_stack.sh qdrant-only
pytest -m "integration and not requires_ollama" --tb=short -v
```

## Ingest vendor CSV

Rows are mapped to a canonical `VendorRecord` using a **column mapping** (logical field → ordered list of candidate header names; first non-empty cell wins). Defaults match common exports and SAP-style files such as `vendor_id`, `name_1` / `name_2` (primary / secondary name), `zip_code`, `vat_no`, `company_code`, `address`, `state`, `date_format`, `eu_member_flag`. Columns not mapped to a known field are stored in `extras` on the record and included in embedding text.

Legacy headers (`legal_name`, `postal_code`, `vat_id`, …) remain in the default candidate lists, so existing CSVs keep working.

To point at another ERP layout, provide a JSON file that **merges** with the defaults (per-key replacement). Set `VENDOR_CSV_COLUMN_MAP_PATH` to that file (see `.env.example`). Example fragment:

```json
{
  "legal_name": ["name_1", "legal_name"],
  "postal_code": ["zip_code", "zip"],
  "vat_id": ["vat_no", "tax_id"]
}
```

```bash
vendor-ingest path/to/vendor_master.csv
# Parse-only check: vendor-ingest --dry-run path/to/vendor_master.csv
# Progress prints to stderr by default; use -q to silence. Interval: --progress-every 1000
```

## REST API and chat UI (Streamlit)

The Streamlit app is an HTTP client to the vendor lookup API. Run **Ollama** and **Qdrant** first, then start the API, then Streamlit.

From this directory (with the venv active and `pip install -e ".[dev]"` done):

```bash
# Terminal 1 — REST API (default http://127.0.0.1:8000; GET /v1/health, GET /v1/status, POST /v1/chat)
vendor-api
# or: python -m vendor_lookup_rag.api
# In containers, set VENDOR_LOOKUP_API_HOST=0.0.0.0

# Terminal 2 — Streamlit (uses VENDOR_LOOKUP_API_BASE_URL, default http://127.0.0.1:8000)
streamlit run src/vendor_lookup_rag/app.py
# or: streamlit run src/vendor_lookup_rag/ui/app.py
```

`app.py` at the package root delegates to `ui/app.py`. **Docker Compose** starts the `api` service on port 8000 and `app` (Streamlit) with `VENDOR_LOOKUP_API_BASE_URL=http://api:8000` — see `[deploy-and-run.md](deploy-and-run.md)`.

## Tests

- **Unit (default):** `pytest` (excludes `@pytest.mark.large_csv`; see below)
- **Large local CSV:** With `data/vendor-data.csv` present, run `pytest -m large_csv` to stream-parse and mock-ingest the full file (tens of seconds for ~60k rows). To run **every** test including `large_csv`, use e.g. `pytest -m "large_csv or not large_csv"` or override `addopts` in `pyproject.toml` for that run.
- **Integration (Qdrant running):** Start Qdrant with `docker compose up -d` in this directory, then run `pytest -m integration` (uses `skip_if_no_qdrant` when `QDRANT_URL` is unreachable).
- **Ollama (optional):** With the Ollama daemon running and the embedding model pulled (`ollama pull` for `EMBEDDING_MODEL` in `.env`), run  
`pytest -m "requires_ollama and integration"` to exercise the real embedding HTTP client (`tests/embedding/test_ollama.py`), and end-to-end retrieval (`tests/retrieval/test_retrieval_integration.py`).

## Retrieval telemetry (optional)

Structured JSON lines per `retrieve_vendors` call: set `VENDOR_LOOKUP_TELEMETRY_LOG_DIR` (writes `vendor_retrieval.jsonl` under that folder), and/or `TELEMETRY_LOG_TO_STDERR` / `TELEMETRY_LOG_TO_STDOUT`, in `.env`. OpenTelemetry can be wired later at the same call sites without changing the retrieval API.

## CI

GitHub Actions: `.github/workflows/vendor-lookup-rag-ci.yml` (runs on push, pull request, and manual dispatch).

- **Unit job:** `pip install -e ".[dev]"` and `pytest` (default markers: no `large_csv`, no `requires_ollama`).
- **Integration job (Qdrant):** starts `docker compose up -d` for Qdrant, waits for `/readyz`, then `pytest -m "integration and not requires_ollama"` so live Qdrant tests run without Ollama. Runs in parallel with the unit job.

