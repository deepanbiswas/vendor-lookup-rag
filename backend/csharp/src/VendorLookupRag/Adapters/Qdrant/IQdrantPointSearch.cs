using Qdrant.Client.Grpc;

namespace VendorLookupRag.Adapters.Qdrant;

/// <summary>Qdrant vector search used by <see cref="QdrantGrpcVectorStore" />; indirection so tests can provide canned gRPC <see cref="ScoredPoint" /> rows without a live server.</summary>
public interface IQdrantPointSearch
{
    Task<IReadOnlyList<ScoredPoint>> SearchAsync(
        string collection,
        float[] vector,
        int limit,
        bool withPayload,
        double? minScore,
        CancellationToken cancellationToken = default);
}
