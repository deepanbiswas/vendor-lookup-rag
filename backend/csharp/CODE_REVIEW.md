# C# backend code review (VendorLookupRag)

**Scope:** `backend/csharp/src` and tests.  
**Date:** 2026-04-22 (review + applied fixes noted inline).

## Summary

The solution follows a **ports and adapters** layout: `IVectorStore` / `ITextEmbedder`, composition in `AddVendorLookupRagCore`, and test fakes. Below are findings and how they were addressed (or deferred).

| # | Area | Finding | Resolution |
|---|------|---------|------------|
| 1 | **DIP (SOLID)** | `VendorLookupAgent` depended on concrete `VendorSearchService` and had an unused `AppOptions` parameter. | **Fixed:** `IVendorSearchService`, constructor takes only abstractions. |
| 2 | **API / security** | `PostChat` returned `e.ToString()` to clients, leaking stack traces. | **Fixed:** `ILogger<Program>` + `IWebHostEnvironment`: log full exception; in production return a generic message; in Development return full detail. (We use `ILogger<Program>` because `VendorApiRouteExtensions` is a `static` class and cannot be the generic `ILogger<>` type parameter.) |
| 3 | **Consistency** | `GetStatus` did not wrap `GetServicesAsync` in `try/catch` unlike `GetHealth`. | **Fixed:** Aligned with `GetHealth` + logging. |
| 4 | **Config** | `QdrantClient` used `https: false` even when `QDRANT_URL` is `https://...`. | **Fixed:** `AppOptions.QdrantUseTls` from URI scheme. |
| 5 | **Hygiene** | `ChatMarkdownFormatter` had an unused `using System.Text;`. | **Fixed:** Removed. |
| 6 | **OCP / composition** | `AddVendorLookupRagCore` registers many services in one block (larger change surface). | **Deferred:** Size is acceptable; split into `Add*`-sections only if the module grows. |
| 7 | **HttpClient** | Singleton `HttpClient` in DI; acceptable for a small API, `IHttpClientFactory` is preferable for long-term DNS/rotation. | **Deferred** (documented in report only). |
| 8 | **DRY (retrieval)** | `RetrievalMinScore` can be applied both in `QdrantClientPointSearch` and `VendorSearchService` (defense in depth). | **Left as-is;** service-side filter remains for non-Qdrant stores. |
| 9 | **Result typing** | `SearchVendorsToolAsync` returns `object` for tool JSON. | **Deferred;** a discriminated result type would be cleaner but is a cross-cutting API change. |

## Positive notes

- **Separation of concerns:** Qdrant wiring split into `IQdrantPointSearch`, `QdrantGrpcVectorStore`, and `QdrantScoredPointMapping`.
- **Tests:** Fakes for `IVectorStore` / `ITextEmbedder`, integration over `WebApplicationFactory`.
- **Configuration:** `AppOptions` + `AppOptionsFactory.FromEnvironment()` is clear and testable.

## Follow-ups (not implemented)

- Introduce `IHttpClientFactory` for Ollama and health `HttpClient` if you need proxy/DNS or multiple logical clients.
- Replace `object` return from the vendor tool with a typed `SearchVendorsResult` (success vs error) for stricter control flow and XML docs on the contract.
