# C# backend (VendorLookupRag)

ASP.NET Core 9 app exposing the same JSON contract as the Python API: `GET /v1/health`, `GET /v1/status`, `POST /v1/chat`. Default listen port is **8001** (`VENDOR_LOOKUP_CSHARP_PORT`; set to **0** for in-memory test runs).

## Build and run

```bash
# From repository root
dotnet run --project backend/csharp/src/VendorLookupRag
# Swagger UI: http://127.0.0.1:8001/swagger
```

Docker: `docker build -f backend/csharp/Dockerfile -t vendor-lookup-csharp:local .` (context = repo root). See root [`docker-compose.csharp.yml`](../../docker-compose.csharp.yml).

## Tests

- **Unit + integration (in-process TestServer):** from repo root

  ```bash
  VENDOR_LOOKUP_CSHARP_PORT=0 dotnet test backend/csharp/VendorLookupRag.sln -c Release
  ```

  (The test suite sets `VENDOR_LOOKUP_CSHARP_PORT=0` in a static constructor so Kestrel does not bind a fixed port; the WebApplicationFactory uses a test host.)

- **Layout:** `tests/VendorLookupRag.Tests/` — model/normalization; **adapters** (`OllamaTextEmbedder` with a canned `HttpMessageHandler`, `QdrantScoredPointMapping` and `QdrantGrpcVectorStore` with `Fakes/FakeQdrantPointSearch` because `QdrantClient.SearchAsync` is not mock-friendly); **agents** (`Agents/VendorLookupAgentTests` with the same fakes and `CannedToolLoopChatClient`); **service** tests; **in-process API** integration: **health** still stubs `HttpClient`; **chat** uses a canned `IChatClient` (`CannedToolLoopChatClient`) because OllamaSharp uses Ollama’s **native** API, not OpenAI-style JSON. Production `IQdrantPointSearch` is implemented by `QdrantClientPointSearch` over gRPC; tests inject a fake in front of the vector store path only in unit tests, not the full `WebApplicationFactory` stack.
- **Chat agent:** [Microsoft.Agents.AI](https://www.nuget.org/packages/Microsoft.Agents.AI) (Agent Framework) + [OllamaSharp](https://www.nuget.org/packages/OllamaSharp) `OllamaApiClient` as `IChatClient` (see `Composition/OllamaChatClientFactory`) + [Microsoft.Extensions.AI](https://www.nuget.org/packages/Microsoft.Extensions.AI) `AIFunctionFactory` for the `search_vendors` tool and `AsAIAgent` on `Agents/VendorLookupAgent` (its static `AgentName` is `"VendorLookupAgent"`; the tool is built in `CreateVendorSearchTool()`).
- **Coverage:** [coverlet](https://github.com/coverlet-coverage/coverlet) collector is referenced; e.g. `dotnet test /p:CollectCoverage=true` for local reports.

## Configuration

Environment variables align with the Python `Settings` names where possible (`OLLAMA_BASE_URL`, `QDRANT_URL`, `QDRANT_COLLECTION`, `CHAT_MODEL`, `EMBEDDING_MODEL`, score thresholds, `RETRIEVAL_MIN_SCORE`, etc.). For the C# Qdrant adapter, `QDRANT_URL` only supplies the **host** (and is used for HTTP health); **gRPC** for `Qdrant.Client` uses the same host with **`QDRANT_GRPC_PORT`** (default **6334**; must match your port mapping if you are not on standard ports, e.g. 6336 on the host for the gRPC map in `docker-compose.csharp.yml`).

See the repository [README.md](../../README.md) for the full variable table and stack layout.
