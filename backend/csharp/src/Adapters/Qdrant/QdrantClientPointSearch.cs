using Qdrant.Client.Grpc;
using QdrantClient = global::Qdrant.Client.QdrantClient;

namespace VendorLookupRag.Adapters.Qdrant;

/// <summary>Default <see cref="IQdrantPointSearch" />: forwards to <see cref="QdrantClient" /> extension <c>SearchAsync</c> (named parameters, score threshold when <paramref name="minScore" /> is set).</summary>
public sealed class QdrantClientPointSearch : IQdrantPointSearch
{
    private readonly QdrantClient _client;

    public QdrantClientPointSearch(QdrantClient client) => _client = client;

    public Task<IReadOnlyList<ScoredPoint>> SearchAsync(
        string collection,
        float[] vector,
        int limit,
        bool withPayload,
        double? minScore,
        CancellationToken cancellationToken = default)
    {
        if (minScore is { } m)
        {
            return _client.SearchAsync(
                collection,
                vector,
                limit: (ulong)limit,
                scoreThreshold: (float)m,
                payloadSelector: withPayload,
                cancellationToken: cancellationToken);
        }

        return _client.SearchAsync(
            collection,
            vector,
            limit: (ulong)limit,
            payloadSelector: withPayload,
            cancellationToken: cancellationToken);
    }
}
