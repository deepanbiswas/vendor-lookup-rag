# Vendor Lookup RAG (local)

Vendor lookup on a vendor master list using **RAG**, **Ollama** (embeddings + chat), **Qdrant**, and an agent that can use a **Python (Pydantic AI)** or **C# (OpenAI-style tools + Ollama)** HTTP API, with a **Streamlit** front end and **TDD**-oriented tests.

This is a **standalone** Git repository.

## Repository layout

| Path | Purpose |
|------|---------|
| `backend/python/` | **Python backend** — package `vendor_lookup_rag` (FastAPI, ingest CLI, domain, Pydantic AI adapters, tests). Install: `pip install -e ".[dev]"` from this directory. |
| `backend/csharp/` | **C# backend** — ASP.NET Core API (same routes as Python). Build/test: `dotnet test backend/csharp/VendorLookupRag.sln`. See [backend/csharp/README.md](backend/csharp/README.md). |
| `frontend/streamlit/` | **Streamlit UI** — installable package `vendor-lookup-frontend` (`vendor_lookup_streamlit`); HTTP client to whatever API you run. |
| `docs/`, `specs/` | Architecture, OpenAPI copy, specifications |
| `plan.md` | Implementation iterations (tracking) |

**Two backends, one UI:** set `VENDOR_LOOKUP_API_BASE_URL` to the Python API (*http://127.0.0.1:8000* by default) or the C# API (*http://127.0.0.1:8001*). **Ingest** (`vendor-ingest`) is Python-only today; both APIs read the same Qdrant collection and Ollama settings.

**Source subpackages (Python, under `backend/python/src/`):** `config/`, `models/`, `csv/`, `normalization/`, `matching/`, `embedding/`, `adapters/`, `vector/`, `retrieval/`, `telemetry/`, `ingestion/`, `agent/`, `api/`, `observability/`, `health/`, and `ui/` (chat display helpers for the **API** response, not the Streamlit app). The C# project mirrors the same **ports** (`ITextEmbedder`, `IVectorStore`) and **adapters** (Ollama embed, Qdrant HTTP search, Ollama chat+tools).

## Quick start (development)

```bash
cd vendor-lookup-rag
python -m venv .venv
source .venv/bin/activate
pip install -e "backend/python[dev]"
# Optional: run Streamlit from the frontend package
pip install -e "frontend/streamlit"
pytest --rootdir=backend/python -c backend/python/pyproject.toml
# Or: cd backend/python && pytest
```

**C# API (optional):** install [.NET 10 SDK](https://dotnet.microsoft.com/download), then from the repo root: `dotnet run --project backend/csharp/src` (or set `VENDOR_LOOKUP_CSHARP_PORT`). Open Swagger at `http://127.0.0.1:8001/swagger`.

**Streamlit:** with the frontend installed and the API running, point `VENDOR_LOOKUP_API_BASE_URL` at the chosen backend and run:

```bash
streamlit run frontend/streamlit/src/vendor_lookup_streamlit/app.py
```

## Local stack

**Docker deployment (Ollama on the host):** see [`docs/deploy-and-run.md`](docs/deploy-and-run.md).

- **Python API + UI:** `docker compose up` using [`docker-compose.yml`](docker-compose.yml) (Qdrant, `api` on 8000, Streamlit on 8501).
- **C# API + UI:** `docker compose -f docker-compose.csharp.yml up --build` (Qdrant on host **6335**, C# API on **8001**, Streamlit on **8502** — avoids clashing with the default compose).

1. **Ollama** (host) — e.g. `ollama pull nomic-embed-text` and a chat model matching `CHAT_MODEL` in `.env` (e.g. `gemma4:e4b`).
2. **Qdrant** — `docker compose up -d` in this directory (`docker-compose.yml`).
3. **Environment** — `cp .env.example .env` and adjust URLs/models.

| Variable | Role | Typical (Python API) | C# API |
|----------|------|----------------------|--------|
| `VENDOR_LOOKUP_API_BASE_URL` | **Streamlit** only — which backend to call | `http://127.0.0.1:8000` | `http://127.0.0.1:8001` |
| `QDRANT_URL` | Ingest, retrieval, both APIs | `http://localhost:6333` | same |
| `OLLAMA_BASE_URL` | Ingest, both APIs | `http://localhost:11434` | same |

**Health checks and integration test env** — as before, use [`scripts/verify_stack.sh`](scripts/verify_stack.sh). Health logic matches [`backend/python/src/health/http.py`](backend/python/src/health/http.py) for Python; the C# service issues the same HTTP checks.

**Integration (Qdrant, no live Ollama in CI for default markers):** start Qdrant, then from `backend/python/`: `pytest -m "integration and not requires_ollama"`.

## Ingest vendor CSV

Unchanged: run `vendor-ingest` from an environment where `backend/python` is installed (see [README](backend/python/README.md) and root `.env`).

## REST API and chat UI (Streamlit)

1. **Python API:** from repo root (with venv): `cd backend/python && vendor-api` (default *http://127.0.0.1:8000*; `VENDOR_LOOKUP_API_HOST=0.0.0.0` in containers).
2. **C# API:** `dotnet run --project backend/csharp/src` (port **8001** by default; override with `VENDOR_LOOKUP_CSHARP_PORT`).

3. **Streamlit:** set `VENDOR_LOOKUP_API_BASE_URL` to the backend you started, then run the `streamlit` command above.

`docker compose` (default file) points Streamlit at the **Python** `api` service (`http://api:8000`). The C# stack uses [`docker-compose.csharp.yml`](docker-compose.csharp.yml) and sets `VENDOR_LOOKUP_API_BASE_URL=http://api-csharp:8001`.

## Tests

- **Python:** from `backend/python/`: `pytest` (excludes `large_csv` and `requires_ollama` per `pyproject.toml` defaults). Markers: `integration`, `requires_ollama`, `large_csv` (see `pyproject.toml`).
- **C#:** from repo root: `dotnet test backend/csharp/VendorLookupRag.sln -c Release` (32+ tests: domain, adapters, services, in-process API; see `backend/csharp/README.md`).

## CI

`.github/workflows/vendor-lookup-rag-ci.yml` — Python install/tests/OpenAPI under `backend/python/`, and **`dotnet test`** for the C# solution.

## Retrieval telemetry (optional)

Unchanged: `VENDOR_LOOKUP_TELEMETRY_LOG_DIR` and related variables apply to the **Python** process where retrieval runs.
