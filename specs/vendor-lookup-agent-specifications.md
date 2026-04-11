# Vendor Lookup Agent Specifications

## 1. Overview
This project automates the verification of vendor details extracted from invoices against a centralized vendor master database. The solution leverages local LLMs and a vector database for semantic search, ensuring high accuracy and data privacy without external SaaS inference APIs. The conversational surface is a **Streamlit** app that calls a **FastAPI** service over HTTP; that service runs the Pydantic AI agent, retrieval tool, and integrations with **Ollama** and **Qdrant** (no third-party cloud RAG backends in the reference stack).

**Architecture:** For components (CSV importer, Qdrant, vendor REST API, agent, retrieval tool, LLM, Streamlit client) and the end-to-end execution flow, see [Vendor Lookup Agent Architecture](../docs/architecture.md).

## 2. Functional Requirements
* **Data Ingestion & Preprocessing:** The system must accept a vendor master list in CSV format. It must clean and normalize the data before vectorization. Ingestion maps CSV columns to a canonical vendor record via a configurable **column mapping** (default lists cover common ERP exports, including alternate header names such as `name_1` / `name_2` for names and `zip_code` / `vat_no` for postal / tax ids). Unmapped columns may be retained in an `extras` payload. Optional JSON overrides merge with defaults when `VENDOR_CSV_COLUMN_MAP_PATH` is set (see project README).
* **Data Embedding & Storage:** The preprocessed records must be converted into vector embeddings and loaded into the local Qdrant vector store.
* **Conversational Input:** The system must expose a Streamlit chat interface allowing users to input partial or full vendor details (e.g., name, city, VAT, ZIP). The UI obtains answers by calling the vendor HTTP API (`POST /v1/chat`); it does not embed the agent or vector clients in-process.
* **Query Normalization:** The system must apply lightweight normalization to user queries (lowercasing, stripping extra spaces, removing punctuation) before querying the database.
* **Semantic Search Execution:** The agent must invoke a retrieval tool to perform a similarity-based vector search on Qdrant using the normalized input.
* **Match Classification & Output:**
    * **Exact Match:** Display full vendor details immediately.
    * **Partial Match:** Return and suggest the top similar vendor candidates for user review.
    * **No Match:** Explicitly state when no matches are found and flag the entry for manual verification.

## 3. Non-Functional Requirements
* **Local Execution:** All inference, embeddings, and database operations must run 100% locally on the host machine.
* **Containerization:** The deployable stack must be describable in a single `docker-compose.yml` (e.g. Qdrant, the vendor API, and the Streamlit UI; Ollama typically on the host for Metal). See [deploy-and-run.md](../deploy-and-run.md).
* **Hardware Optimization:** LLM and embedding generation must utilize Apple's Metal Performance Shaders (MPS) for low latency.
* **Testability (TDD/SDD):** The architecture must be highly modular. Data ingestion, normalization, and retrieval logic must be broken down into individually testable Python functions.

## 4. Tech Stack
* **LLM & Embedding Provider:** Ollama (running locally, optimized for Apple Silicon/Metal).
* **Large Language Model:** Gemma 4 (E4B or 26B MoE) for advanced agentic reasoning and tool execution.
* **Embedding Model:** `nomic-embed-text` or `mxbai-embed-large` via Ollama.
* **Vector Database:** Qdrant (Self-hosted via Docker).
* **Orchestration Framework:** Pydantic AI (Code-first Python agent framework).
* **User Interface:** Streamlit (Python-native frontend) as an HTTP client to a thin **FastAPI** REST layer (`vendor_lookup_rag.api`) that runs the agent and tools.
* **HTTP API:** FastAPI + Uvicorn (`vendor-api`), JSON REST for chat and health/status (`/v1/chat`, `/v1/health`, `/v1/status`).
* **Caching Layer (Optional):** Redis (Self-hosted via Docker).
* **Containerization:** Docker & Docker Compose.
* **Programming Language:** Python 3.11+.

## 5. Scenarios and traceability

<a id="s1-package-version"></a>

### S1 — Package is versioned

- **Given** the installed package `vendor_lookup_rag`
- **When** the version is read
- **Then** it is a non-empty semantic version string

Covered by `tests/test_package_smoke.py`.
