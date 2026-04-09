# Vendor Lookup Agent Architecture

## 1. System overview

The Vendor Lookup Agent is a modular, local-first RAG (Retrieval-Augmented Generation) pipeline. It orchestrates the flow of data from user input through a Streamlit UI to vector search and final LLM synthesis, ensuring fast and accurate vendor matching.

## 2. Core components

### A. CSV importer (data pipeline)

* **Function:** One-time (or batch) ingestion process.
* **Action:** Reads the raw vendor master CSV, applies lightweight text normalization (lowercasing, punctuation removal), generates vector embeddings via Ollama, and inserts the records into the Qdrant vector store.

### B. Vector store (Qdrant)

* **Function:** Scalable similarity search engine.
* **Action:** Stores preprocessed vendor records as vector embeddings. Executes high-speed nearest-neighbor searches based on the query vectors it receives from the retrieval tool.

### C. Vendor lookup agent (orchestration layer)

* **Function:** The central orchestration layer, built using Pydantic AI.
* **Action:** (1) Receives natural language queries containing vendor details from the user. (2) Determines if the input requires clarification or is ready for search. (3) Invokes the vendor retrieval tool. (4) Evaluates the search results (exact, partial, or no match). (5) Formats the final response for the user.

### D. Vendor retrieval tool (tool execution)

* **Function:** The Python tool invoked by the Pydantic AI agent to interface with retrieval.
* **Action:** Normalizes the user's input, converts it into an embedding via Ollama, and queries Qdrant to return the top *N* vendor matches.

### E. LLM engine (Ollama chat model)

* **Function:** Local inference engine.
* **Action:** Powers the reasoning capabilities of the agent, processing the context retrieved from Qdrant and generating the human-readable conversational output.

### F. User interface (Streamlit)

* **Function:** The front-end conversational interface.
* **Action:** Captures user queries using `st.chat_input` and renders the agent output using `st.chat_message`.

## 3. High-level execution flow

1. **Submit:** The user submits a vendor query through the Streamlit chat interface.
2. **Process and route:** The Pydantic AI agent receives the input and invokes the vendor retrieval tool.
3. **Embed and search:** The retrieval tool embeds the query and performs a vector similarity search on Qdrant.
4. **Retrieve:** Qdrant returns the top *N* candidate records.
5. **Analyze:** The agent analyzes the candidates alongside the original query using the chat LLM.
6. **Respond:** The agent formats the result (exact, partial, or no match) and Streamlit renders the final vendor details or suggestions to the user.

## 4. Solution architecture diagram

```mermaid
graph TD
    %% Styling Definitions
    classDef user fill:#003366,stroke:#333,stroke-width:2px,color:#fff;
    classDef ui fill:#ff4b4b,stroke:#333,stroke-width:2px,color:#fff;
    classDef agent fill:#4caf50,stroke:#333,stroke-width:2px,color:#fff;
    classDef tool fill:#2196f3,stroke:#333,stroke-width:2px,color:#fff;
    classDef llm fill:#9c27b0,stroke:#333,stroke-width:2px,color:#fff;
    classDef db fill:#ff9800,stroke:#333,stroke-width:2px,color:#fff;
    classDef file fill:#eee,stroke:#333,stroke-width:1px,color:#1a1a1a,stroke-dasharray: 5 5;

    %% User
    U[User - Invoice Processor]:::user

    %% Streamlit UI
    UI(Streamlit UI - Chat Interface):::ui

    %% Orchestration Layer
    subgraph Python Application Environment
        A{Pydantic AI Agent Orchestrator}:::agent
        T[Vendor Retrieval Tool - Python Function]:::tool
    end

    %% Local Inference Server
    subgraph Local Inference - Apple Metal
        O_LLM(Ollama - Gemma 4 Local LLM):::llm
        O_EMB(Ollama - nomic-embed-text):::llm
    end

    %% Database
    DB[(Qdrant Vector Store - Self-Hosted)]:::db

    %% Offline Data Ingestion Pipeline
    subgraph Data Ingestion
        CSV_File([Vendor Master CSV]):::file
        Ingest[CSV Importer - Python Script]:::tool
    end

    %% Live RAG Workflow Connections
    U -->|1. Submits vendor query| UI
    UI -->|2. Passes user input| A

    A -->|3. Invokes as tool| T
    T -->|4. Requests query embedding| O_EMB
    O_EMB -.->|5. Returns vector| T

    T -->|6. Performs similarity search| DB
    DB -.->|7. Returns Top N matches| T

    T -->|8. Returns search results| A

    A -->|9. Prompts query and top matches| O_LLM
    O_LLM -.->|10. Generates response| A

    A -->|11. Formats and returns response| UI
    UI -->|12. Displays matched vendors| U

    %% Ingestion Workflow Connections
    CSV_File -.->|Preprocess and Normalize| Ingest
    Ingest -.->|Generate Document Embeddings| O_EMB
    Ingest -.->|Load Vectors and Payload| DB

    %% Link styles (white strokes for visibility on dark backgrounds)
    linkStyle default stroke:#fff,stroke-width:1.5px;
```
