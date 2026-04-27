# Vendor Lookup RAG

**Look up vendors from natural-language questions** against your own **vendor master list**, using a local **vector store** and **language model**—so invoice or procurement teams can verify a company name, address, or tax ID without sending data to a cloud RAG product.

This repository is **self-contained**: a **Streamlit** chat app talks to a small **HTTP API** (you can run the API in **Python** or **C#**), which in turn uses **Ollama** (embeddings + chat) and **Qdrant** (similarity search). Ingesting your CSV into Qdrant is done with a **Python** command-line tool.

---

## What to read first

| If you want to… | Open |
|-----------------|------|
| **Run the app** in Docker (simplest) | [docs/deploy-and-run.md](docs/deploy-and-run.md) — step-by-step, macOS/Windows, both compose stacks |
| **Understand the design** (ports, adapters, two backends) | [docs/architecture.md](docs/architecture.md) |
| **See the product requirements** (what the software must do) | [specs/vendor-lookup-agent-specifications.md](specs/vendor-lookup-agent-specifications.md) |
| **See how it was built** (iterations, commands, SDD for contributors) | [specs/vendor-lookup-agent-plan.md](specs/vendor-lookup-agent-plan.md) |

---

## How it works (one minute)

1. You **load a vendor master CSV** into Qdrant (embeddings are computed for you).  
2. A user **chats in the browser** (Streamlit).  
3. Each message goes to the **vendor API** (`/v1/chat`); an **agent** calls a **search tool** that runs semantic search in Qdrant, then the model answers.  
4. The UI shows **match quality** (exact, partial, or no match) so a human can decide next steps.

**Ollama** usually runs **on your machine** (good performance on Apple Silicon). **Qdrant** and the optional **API + Streamlit** containers are started with **Docker Compose**.

There are **two** API implementations (same JSON routes, different process): **Python (FastAPI)** and **C# (ASP.NET Core)**. Ingestion is **Python-only**. The chat UI just needs `VENDOR_LOOKUP_API_BASE_URL` pointed at whichever API you started.

---

## What you need

- **Python 3.11+** — for ingest, the Python API, and tests.  
- **Docker** (Docker Desktop is fine) — to run Qdrant and, if you like, the API and Streamlit in containers.  
- **Ollama** — [ollama.com](https://ollama.com); install on the **host** for typical Mac setups.  
- **.NET 10 SDK** — only if you work on or run the **C#** API locally.

---

## Path A: Run with Docker (good first run)

1. **Clone** this repo and `cd` into it.  
2. **Install Ollama** on the host and **pull** the embedding and chat models your `.env` will use (see `.env.example` for names). The repo has helper scripts under `scripts/`; full detail is in [docs/deploy-and-run.md](docs/deploy-and-run.md).  
3. **Create config:** `cp .env.example .env` and adjust if needed.  
4. **Start the stack** (Qdrant + Python API + Streamlit):  
   `docker compose up --build -d`  
5. **Ingest** your vendor CSV (example assumes data under `data/`): see the *Ingest* section in [docs/deploy-and-run.md](docs/deploy-and-run.md) (`docker compose run --rm` … `vendor-ingest`).  
6. Open the **Streamlit** URL from the deploy doc (port **8501** for the default file). The UI talks to the Python API on **8000** by default when using `docker-compose.yml`.

**C# API instead:** use `docker compose -f docker-compose.csharp.yml up --build -d` — different **host** ports (e.g. Qdrant **6335**, API **8001**, UI **8502**). Only run **one** Qdrant-backed stack at a time if they share a volume. Details: [docs/deploy-and-run.md](docs/deploy-and-run.md).

**Verify** services: optional script [scripts/verify_stack.sh](scripts/verify_stack.sh) (Ollama + Qdrant + optional API check).

---

## Path B: Develop on the host (no Docker, or partial)

From the **repository root**, with a virtual environment activated:

```bash
pip install -e "backend/python[dev]"
pip install -e "frontend/streamlit"
cd backend/python && pytest
```

Run the **Python API**: `cd backend/python && vendor-api` (or `python -m vendor_lookup_rag.api`) — default **http://127.0.0.1:8000**.  
Run **Streamlit**: `streamlit run frontend/streamlit/src/vendor_lookup_streamlit/app.py` and set `VENDOR_LOOKUP_API_BASE_URL` to that API.  
**Ingest** (from `backend/python` with env vars pointing at Ollama/Qdrant): `vendor-ingest /path/to/vendors.csv`.

**C# API (optional):** from repo root, `dotnet run --project backend/csharp/src` — see [backend/csharp/README.md](backend/csharp/README.md).

---

## Important environment variables (overview)

| Variable | Role |
|----------|------|
| `OLLAMA_BASE_URL` | Where the app finds Ollama (e.g. `http://localhost:11434` on the host) |
| `QDRANT_URL` | Qdrant HTTP API (ingest, Python path; C# also uses gRPC + related settings) |
| `VENDOR_LOOKUP_API_BASE_URL` | **Streamlit only** — which vendor API to call (Python **8000** or C# **8001** locally) |

Copy `.env.example` to `.env` and read comments there; Compose overrides some values inside containers.

---

## Repository layout (short)

| Location | What it is |
|----------|------------|
| [backend/python/](backend/python/) | Python package: ingest, FastAPI app, RAG domain code, **pytest** suite |
| [backend/csharp/](backend/csharp/) | Optional **.NET 10** API, same HTTP contract as the Python service |
| [frontend/streamlit/](frontend/streamlit/) | Streamlit UI package (HTTP **client** only) |
| [docs/](docs/) | Architecture, deploy/run, security, OpenAPI copy |
| [specs/](specs/) | Product spec + implementation / iteration plan |

Deeper C# notes: [backend/csharp/README.md](backend/csharp/README.md). Python packaging notes: [backend/python/README.md](backend/python/README.md).

---

## Ingesting your vendor CSV

Use the **`vendor-ingest`** command (Python env, after `pip install -e "backend/python[dev]"`).

- Required columns include **`vendor_id`** and **`legal_name`**; optional fields and **column mapping** (including external JSON) are covered in the **CSV format** section of [specs/vendor-lookup-agent-plan.md](specs/vendor-lookup-agent-plan.md) and in `.env.example`.  
- Full Docker examples: [docs/deploy-and-run.md](docs/deploy-and-run.md).

---

## Tests and CI

- **Python:** from `backend/python/`, run `pytest` (default excludes slow/large tests; see `pyproject.toml` markers: `integration`, `requires_ollama`, `large_csv`).  
- **C#:** from repo root, `dotnet test backend/csharp/VendorLookupRag.sln -c Release` (needs .NET 10).  
- **CI:** [`.github/workflows/vendor-lookup-rag-ci.yml`](.github/workflows/vendor-lookup-rag-ci.yml) runs both.

---

## Security and telemetry

- Dependency and surface notes: [docs/security-notes.md](docs/security-notes.md).  
- Optional Python retrieval telemetry: env vars like `VENDOR_LOOKUP_TELEMETRY_LOG_DIR` (see code and settings).

---

## License

The package metadata in this repository declares a **proprietary** license. Use the terms your organization applies to this codebase, or the `license` value in [backend/python/pyproject.toml](backend/python/pyproject.toml) as a hint for tooling.
