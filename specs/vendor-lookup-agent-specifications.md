# Vendor Lookup Agent — Product specification

**Document type:** Product / system requirements (specification)  
**Method:** Spec-driven development (SDD) — *what* the system must do and *under what constraints*; the execution plan, implementation, and test mapping live in a separate plan document, not in this file.

**Relationship to the plan:** A companion **implementation and execution plan** decomposes these requirements into iterations, deliverables, and test strategy. This specification does not prescribe directory layout, programming language constructs, or version-control structure.

**Normative terms:** The keywords **MUST**, **MUST NOT**, **SHALL**, **SHALL NOT**, **SHOULD**, and **MAY** are interpreted as requirements levels per common RFC-style usage. **MUST** / **SHALL** indicate mandatory requirements unless stated otherwise.

---

## 1. Purpose and scope

### 1.1 Problem

Invoice processing staff need to confirm whether a vendor name, address, or tax identifier from an invoice line matches a row in a central **vendor master** list. Manual lookup is slow; this system supports that workflow with **semantic search** and a **conversational** way to ask for candidate matches, while keeping sensitive data and inference under the operator’s control (no required third-party RAG or inference APIs in the reference deployment).

### 1.2 In scope

- Ingesting a vendor master dataset from **CSV** with cleaning, mapping, and normalization.
- Generating **embeddings**, storing them in a **self-hosted vector index**, and running **similarity search** for user questions.
- Classifying search outcomes (exact / partial / no match) for presentation to the user.
- Exposing **vendor lookup** to users through a **web chat** experience that **calls a vendor HTTP API** (no in-browser embedding of the full agent/retrieval stack in the chat client).
- A **JSON HTTP API** for health, system status, and **chat** that can be implemented more than once, as long as the **public contract and behavior** for those endpoints are aligned.
- A **local** deployment option where inference and the vector store run on infrastructure controlled by the operator (see constraints).

### 1.3 Out of scope (reference product)

- Mandatory use of a specific cloud LLM or managed vector service as the default path.
- Storing or processing data that is not part of the vendor-lookup and invoice-verification use case, except as required for operation (logs, health).
- A requirement that the chat UI and the vendor API be deployed in the same operating-system process (they **must** interact over the network in the reference architecture).

---

## 2. Definitions

| Term | Meaning |
|------|--------|
| **Vendor master** | The authoritative list of known vendors, typically with identifiers, names, and address or tax fields. |
| **Ingestion** | The batch or repeatable process that reads a vendor master, normalizes records, creates embeddings, and updates the vector index. |
| **User query** | A natural-language or semi-structured description of a vendor to look up, as entered in the chat UI. |
| **Vector index** | A similarity-search store holding embedding vectors and retrievable records derived from the vendor master. |
| **Vendor HTTP API** | The service that exposes the chat and health endpoints defined in this specification, independent of the chat client. |
| **Agent** | The component that uses a language model and one or more tools to decide when to run retrieval and how to use results in the same conversational turn, within the reference design. |
| **Ports and adapters (hexagonal)** | A design expectation: business-oriented behavior depends on **stable interfaces** (ports); concrete integrations (embedder, index, LLM) are **swappable adapters** so tests and future backends do not require rewriting the core flow. The specification requires **separation of concerns**; it does not name particular interface types. |

---

## 3. Functional requirements

**FR-01 — Vendor master as CSV**  
The system **MUST** accept vendor master data as one or more **CSV** inputs suitable for import.

**FR-02 — Preprocessing and mapping**  
The system **MUST** normalize and map CSV columns to a **canonical** vendor record shape, including support for **configurable column mapping** and sensible defaults for common column naming variants. Unmapped source columns **MAY** be retained in auxiliary fields when that aids auditability.

**FR-03 — Embeddings and index**  
The system **MUST** create vector **embeddings** for prepared records and **MUST** store and query them in a **vector index** with similarity search. Ingestion **MUST** be able to add or update indexed content from a prepared master list.

**FR-04 — Query normalization**  
The system **MUST** apply **lightweight normalization** to user queries (e.g. case folding, whitespace, punctuation) before using them for retrieval, consistent with the same rules used in preprocessing where applicable.

**FR-05 — Agent-driven retrieval**  
The system **MUST** use an **agent** (language model with tools) such that the **retrieval** step is reached through a defined **tool** or equivalent mechanism that performs **semantic search** on the index using a normalized form of the user’s input. The system **MUST NOT** require the user to manually call a separate “search” HTTP endpoint in the main chat flow.

**FR-06 — Match classification and presentation**  
The system **MUST** distinguish outcomes at least as **exact match**, **partial match (candidates)**, and **no match**, and **MUST** present results so the user can act (confirm, pick among candidates, or know manual review is required).

**FR-07 — Web chat and API separation**  
The system **MUST** provide a **browser-accessible** conversational UI for the workflow. That UI **MUST** obtain results by **calling the vendor HTTP API** over the network. The UI **MUST NOT** be required to embed the agent, embedding client, or direct index client in-process; those responsibilities belong to the vendor API process (or processes) behind that API.

**FR-08 — Vendor HTTP API contract**  
The system **MUST** expose, at minimum:

- a **readiness/health** endpoint;
- a **status** endpoint summarizing dependencies relevant to the workflow (e.g. language-model and index availability) in a form suitable for a dashboard; and  
- a **chat** endpoint that accepts a user message and returns a machine-processable response that includes the assistant’s display content and, where applicable, a trace of tool use for supportability.

**FR-09 — Ingestion availability**  
At least one supported path **MUST** exist to run ingestion from a command line or operator-automation context (e.g. CI or scripts), independent of the chat session.

**FR-10 — Multiple conforming server implementations (optional but supported)**  
The product **MAY** ship more than one server stack that implements **FR-08** with the **same** public HTTP semantics for the same routes. If two implementations are offered, the conversational UI and operational procedures **MUST** be able to target either, by configuration, without changing the UI code beyond configuration of the **base URL** of the vendor API. A **conforming** second implementation **MUST** still rely on the same **external** contracts for the language model and the vector index (no duplicate ingestion model).

**FR-11 — Ingestion ownership (when FR-10 applies)**  
If a second server implementation exists, **ingestion of the vendor master and updates to the vector index** **SHALL** remain the responsibility of the **primary** reference implementation, unless explicitly superseded by a future specification revision. The alternate server **MUST** read the same index semantics and payload expectations so that, after a successful ingest, either server can answer consistently.

---

## 4. Non-functional requirements

**NFR-01 — Local execution (reference stack)**  
The reference deployment **MUST** be able to run with **inference, embeddings, and vector data** fully under operator-controlled infrastructure, without requiring a subscription to a third-party inference or vector service for core operation.

**NFR-02 — Testability and modularity**  
The architecture **MUST** allow **unit tests** for core logic (normalization, classification, mapping, retrieval orchestration) **without** live network access to the language model or the vector service where practical. The design **SHALL** use clear boundaries (ports and adapters) so that implementations of the embedding, index, and LLM can be **substituted in tests and in the field** without changing the HTTP contract.

**NFR-03 — Containerized deployment**  
The reference deployment **MUST** be describable using **container** definitions so that the vector service and, where applicable, the vendor API and chat client can be started in a **repeatable** way. The **language-model runtime** (when not embedded in those containers) **MUST** remain configurable so operators can run it on the **host** for best hardware use on supported platforms.

**NFR-04 — Observability**  
The system **MUST** support **structured** or otherwise reviewable **logging** for request handling and for failures in dependency calls, suitable for local troubleshooting.

**NFR-05 — Configuration**  
Runtime behavior (model endpoints, index location, collection names, thresholds) **MUST** be **configurable** through deployment-time settings (e.g. environment and configuration files), not hard-coded compile-time constants, except for safe defaults.

**NFR-06 — Version and release identity**  
Distributable components **MUST** expose a **version** or release identifier that support staff can use to reason about compatibility and report defects.

**NFR-07 — Security posture (baseline)**  
Dependencies and runtime images **SHOULD** be **maintainable and patchable**; the project **SHALL** document expectations for keeping dependency bases current for known issues (details belong to security and operations documentation, not this file).

**NFR-08 — Continuous verification**  
The project **MUST** maintain an automated **build** and **regression** path that runs **unit** tests and, as appropriate, **integration** tests against real or containerized services, so that changes do not silently break the public HTTP contract or ingestion.

---

## 5. Stated technology and product-line constraints (this repository)

The following are **product decisions** for the reference line of this project. They are **not** file names, module names, or code—only **which classes of system** the implementation **MUST** or **MAY** use so that the requirements above are satisfiable in a local-first product.

- **Vector database:** The reference product **MUST** use **Qdrant** as the self-hosted vector store for semantic search, operated under the customer’s or operator’s control in the default deployment.
- **Language and embedding runtime:** The reference product **MUST** use **Ollama** for on-machine embedding and chat, accessed through its supported HTTP interface from the components that need inference.
- **Web user interface for chat:** The reference product **MUST** ship a **Streamlit**-based chat client that complies with **FR-07** (remoting to the vendor API). Replacements with equivalent remoting behavior **MUST** be an explicit spec change.
- **Primary application language for ingestion and the primary API:** **Python 3.11+** is required for the canonical ingestion path and at least one full vendor-API server.
- **Optional second vendor API server:** A **.NET** (current supported release) server **MAY** implement the same public HTTP contract as the primary server for the same data plane; it **MUST NOT** be required to duplicate the ingestion path under **FR-11**.

---

## 6. Scenarios (acceptance-style)

Scenarios are written for **traceability** to the functional requirements. Implementation and test cases in the project plan **map to** these scenario ids.

### S1 — Ingest and search path

- **Given** a valid vendor master CSV and a running index and language model per deployment instructions  
- **When** ingestion completes and a user sends a **chat** message describing a vendor  
- **Then** the system returns a **chat** response that includes retrieval-backed content consistent with **FR-05** and **FR-06** (at least one of exact, partial, or no-match style outcome).

### S2 — Health and status for operators

- **Given** a running deployment  
- **When** a client calls the **health** and **status** endpoints **FR-08**  
- **Then** the responses are sufficient to determine whether the system can serve chat and whether key dependencies are reachable, without opening the database or language-model processes directly.

### S3 — Chat without colocated agent in the browser client

- **Given** the web chat and vendor API are deployed in separate services or processes as allowed by **FR-07**  
- **When** a user sends a message  
- **Then** the chat path succeeds using **only** the documented **HTTP** interface to the vendor API for that turn, consistent with **FR-07** and **FR-08**.

<a id="s4-version-discoverability"></a>

### S4 — Version discoverability (supports NFR-06)

- **Given** a correctly installed or built deliverable of the product  
- **When** an operator or an automated process queries the product’s stated version or release information  
- **Then** a non-empty, meaningful version or release string is available for support and change tracking.

### S5 — Optional dual server parity (only if FR-10 / FR-11 apply)

- **Given** two conforming vendor API implementations are available and the index has been updated through the **designated** ingestion path  
- **When** the chat client is configured to the base URL of **either** implementation  
- **Then** the same class of user message **SHALL** yield **compatible** health/status semantics and **substantively equivalent** chat results for the same data (allowing for minor presentation differences that do not affect business decisions).*

\*Exact numerical parity of scores and ordering **MAY** vary if underlying libraries differ, but the user-facing classification (**FR-06**) must remain aligned.

---

## 7. Assumptions

- Operators can install or run a **local language-model** runtime and a **self-hosted** vector service as required by deployment documentation.
- Network connectivity exists between the chat client, the vendor API, the language model, and the vector index in the target environment.
- CSV vendor masters are **authorized** for use in the system and are **sufficiently** complete for the intended **exact** / **partial** matching story.

---

## 8. Traceability (requirements ↔ scenarios)

| Requirement ids | Scenarios that exercise them (primary) |
|-----------------|-------------------------------------------|
| FR-01 – FR-04, FR-09 | S1 (ingest path) |
| FR-05, FR-06 | S1 |
| FR-07, FR-08 | S1, S2, S3 |
| FR-10, FR-11 | S5 (if applicable) |
| NFR-06, version identity | S4 |

The **execution plan** shall maintain a mapping from automated tests to these **requirements and scenario** identifiers; that mapping is **out of scope** of this document.

---

*End of product specification. Implementation details, technology choices for default stacks, repository layout, and test file locations belong in separate planning and design artifacts.*
