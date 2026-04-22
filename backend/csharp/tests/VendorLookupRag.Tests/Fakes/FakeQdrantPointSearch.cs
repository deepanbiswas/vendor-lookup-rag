using Qdrant.Client.Grpc;
using VendorLookupRag.Adapters.Qdrant;

namespace VendorLookupRag.Tests.Fakes;

public sealed class FakeQdrantPointSearch : IQdrantPointSearch
{
    public IReadOnlyList<ScoredPoint> Canned { get; set; } = Array.Empty<ScoredPoint>();

    public List<(string Collection, float[] Vector, int Limit, bool WithPayload, double? MinScore)> Calls { get; } = new();

    public Task<IReadOnlyList<ScoredPoint>> SearchAsync(
        string collection,
        float[] vector,
        int limit,
        bool withPayload,
        double? minScore,
        CancellationToken cancellationToken = default)
    {
        Calls.Add((collection, vector, limit, withPayload, minScore));
        return Task.FromResult(Canned);
    }
}
