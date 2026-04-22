# Vendor Lookup Agent Architecture

## 1. System overview

The Vendor Lookup Agent is a modular, local-first RAG (Retrieval-Augmented Generation) pipeline. The **Streamlit** UI is a thin **HTTP client** to a **FastAPI** service that hosts the Pydantic AI agent, retrieval tool, and connections to **Ollama** and **Qdrant**. This keeps inference and vector search behind a stable REST surface while preserving the same chat behavior as the former in-process design.

Domain code depends on **ports** (`TextEmbedder`, `VectorStore`, `VendorAgentRunner`); **adapters** wire the defaults (**Ollama** HTTP embeddings, **Qdrant** via `qdrant-client`, **Pydantic AI** runner wrapping chat). Factories and `build_production_runtime()` in the API layer compose them. See **[adapter-switching.md](adapter-switching.md)** for swapping implementations.

**Operations:** Run order (Ollama and Qdrant up, then the vendor API, then Streamlit), Docker Compose layout, health scripts, and environment variables for local development and integration tests are described in the repository **[README.md](../README.md)**.

## 2. Core components

### A. CSV importer (data pipeline)

* **Function:** One-time (or batch) ingestion process.
* **Action:** Reads the raw vendor master CSV, applies lightweight text normalization (lowercasing, punctuation removal), generates vector embeddings via Ollama, and inserts the records into the Qdrant vector store.

### B. Vector store (Qdrant)

* **Function:** Scalable similarity search engine.
* **Action:** Stores preprocessed vendor records as vector embeddings. Executes high-speed nearest-neighbor searches based on the query vectors it receives from the retrieval tool (via the API process).

### C. Vendor lookup REST API (FastAPI)

* **Function:** Thin HTTP layer exposing chat, status, and machine-readable API metadata.
* **Action:** Builds `AgentDeps` (embedder + vector store), runs `VendorAgentRunner.run_sync`, and returns pre-rendered markdown and trace text. Exposes **GET `/v1/health`** (Ollama/Qdrant only), **GET `/v1/status`** (health plus model and threshold metadata for the Streamlit sidebar), and **POST `/v1/chat`**. **OpenAPI 3.x** is served at **`GET /openapi.json`** with **Swagger UI** at **`GET /docs`**; a copy of the spec is also kept at **[openapi.json](openapi.json)** for review and CI.

### D. Vendor lookup agent (orchestration layer)

* **Function:** The central orchestration layer, built using Pydantic AI (runs inside the API process).
* **Action:** (1) Receives natural language queries containing vendor details. (2) Invokes the vendor retrieval tool. (3) Evaluates the search results (exact, partial, or no match). (4) Returns structured tool output; the API maps that to display strings.

### E. Vendor retrieval tool (tool execution)

* **Function:** The Python tool invoked by the Pydantic AI agent to interface with retrieval (`search_vendors` → `search_vendors_tool_body`).
* **Action:** Normalizes the user's input, calls `retrieve_vendors` using the injected **`TextEmbedder`** and **`VectorStore`** ports (default adapters: Ollama embeddings + Qdrant search), classifies hits, and returns structured **`SearchVendorToolResult`** data for the API to render.

### F. LLM engine (Ollama chat model)

* **Function:** Local inference engine.
* **Action:** Powers the agent (OpenAI-compatible HTTP to Ollama under the API process).

### G. User interface (Streamlit)

* **Function:** The front-end conversational interface.
* **Action:** Captures user queries using `st.chat_input`, calls **POST `/v1/chat`** for each turn, and renders responses using `st.chat_message`. Sidebar uses **GET `/v1/status`** (cached) instead of calling Ollama/Qdrant health checks directly.

## 3. High-level execution flow

1. **Submit:** The user submits a vendor query through the Streamlit chat interface.
2. **REST call:** Streamlit sends the message to the vendor API (**POST `/v1/chat`**).
3. **Process and route:** The Pydantic AI agent receives the input and invokes the vendor retrieval tool.
4. **Embed and search:** The retrieval tool embeds the query and performs a vector similarity search on Qdrant.
5. **Retrieve:** Qdrant returns the top *N* candidate records.
6. **Analyze:** The chat model runs against Ollama (OpenAI-compatible API); it issues a tool call, consumes the tool result, and may run another completion to finish the turn (e.g. assistant text `"OK"` per system prompt).
7. **Respond:** The API returns display markdown and trace text; Streamlit renders the vendor details or suggestions to the user.

## 4. Solution architecture diagram

```mermaid
graph TD
    classDef user fill:#003366,stroke:#333,stroke-width:2px,color:#fff;
    classDef ui fill:#ff4b4b,stroke:#333,stroke-width:2px,color:#fff;
    classDef api fill:#607d8b,stroke:#333,stroke-width:2px,color:#fff;
    classDef agent fill:#4caf50,stroke:#333,stroke-width:2px,color:#fff;
    classDef tool fill:#2196f3,stroke:#333,stroke-width:2px,color:#fff;
    classDef llm fill:#9c27b0,stroke:#333,stroke-width:2px,color:#fff;
    classDef db fill:#ff9800,stroke:#333,stroke-width:2px,color:#fff;
    classDef file fill:#eee,stroke:#333,stroke-width:1px,color:#1a1a1a,stroke-dasharray: 5 5;
    classDef deps fill:#37474f,stroke:#333,stroke-width:2px,color:#fff;

    U[User - Invoice Processor]:::user
    UI(Streamlit UI - HTTP client):::ui
    REST[Vendor Lookup REST API - FastAPI]:::api

    subgraph apiProc [API process — runtime: AgentDeps + PydanticAiVendorAgent]
        DEPS[AgentDeps — TextEmbedder + VectorStore]:::deps
        A{Pydantic AI Agent}:::agent
        T[Vendor retrieval tool — retrieve_vendors]:::tool
    end

    subgraph LocalInference [Local inference]
        O_LLM(Ollama - chat):::llm
        O_EMB(Ollama - embeddings):::llm
    end

    DB[(Qdrant)]:::db

    subgraph DataIngestion [Data ingestion]
        CSV_File([Vendor Master CSV]):::file
        Ingest[CSV Importer CLI]:::tool
    end

    U -->|1. Submits query| UI
    UI -->|2. POST /v1/chat JSON| REST
    REST --> DEPS
    DEPS --> A
    A -->|3. Tool call| T
    T -->|4. Embed via port - POST /api/embed| O_EMB
    O_EMB -.->|5. Vector| T
    T -->|6. Search via port| DB
    DB -.->|7. Top N| T
    T -->|8. Tool result| A
    A -->|9–10. Chat completions / tool loop| O_LLM
    O_LLM -.->|Model output| A
    A -->|11. Response payload| REST
    REST -->|12. JSON display + trace| UI
    UI -->|13. Renders| U

    UI -.->|GET /v1/status| REST

    CSV_File -.->|Normalize| Ingest
    Ingest -.->|Embeddings| O_EMB
    Ingest -.->|Upsert| DB

    linkStyle default stroke:#fff,stroke-width:1.5px;
```

Default adapters: **OllamaEmbedder** (embeddings) and **QdrantVectorStore** (index). The chat model uses **OpenAI-compatible** HTTP to Ollama inside the Pydantic AI adapter.

## 5. Sequence diagram (user query)

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant St as Streamlit
    participant Api as VendorAPI
    participant Agent as PydanticAgent
    participant Tool as search_vendors
    participant Oe as Ollama_embed
    participant Qd as Qdrant
    participant Oc as Ollama_chat

    User->>St: Enter vendor text
    St->>St: Queue prompt and rerun
    St->>Api: POST /v1/chat
    Api->>Agent: run_sync(message, deps)
    Agent->>Oc: Chat completion (model plans tool call)
    Oc-->>Agent: tool_calls e.g. search_vendors
    Agent->>Tool: search_vendors(user_query)
    Tool->>Oe: HTTP POST /api/embed
    Oe-->>Tool: embedding vector
    Tool->>Qd: vector search (qdrant-client)
    Qd-->>Tool: top-K records
    Tool-->>Agent: SearchVendorToolResult
    Agent->>Oc: Chat completion (tool result in context)
    Oc-->>Agent: assistant message e.g. OK
    Agent-->>Api: run result
    Api->>Api: assistant_markdown_from_run + format_agent_run_trace
    Api-->>St: JSON display_markdown, trace_text
    St-->>User: Render markdown and optional trace
```

## 6. Protocol summary

| Path | Mechanism |
|------|-----------|
| Streamlit to API | HTTP REST (JSON), `httpx` client (`GET /v1/status`, `POST /v1/chat`) |
| Browser or tooling to API | **OpenAPI 3.x** at `/openapi.json`, **Swagger UI** at `/docs` |
| API to Ollama | HTTP (embed + OpenAI-compatible chat) |
| API to Qdrant | HTTP via `qdrant-client` |
| Ingestion CLI to Ollama/Qdrant | Same HTTP stacks as above (no Streamlit) |
