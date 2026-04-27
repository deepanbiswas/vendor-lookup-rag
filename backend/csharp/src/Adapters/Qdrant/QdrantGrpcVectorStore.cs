using VendorLookupRag.Configuration;
using VendorLookupRag.Models;
using VendorLookupRag.Ports;

namespace VendorLookupRag.Adapters.Qdrant;

/// <summary>Vector search over Qdrant using gRPC (default port 6334). Delegates the wire call to <see cref="IQdrantPointSearch" /> (production: <see cref="QdrantClientPointSearch" />).</summary>
public sealed class QdrantGrpcVectorStore : IVectorStore
{
    private readonly IQdrantPointSearch _qdrant;
    private readonly AppOptions _opt;

    public QdrantGrpcVectorStore(IQdrantPointSearch qdrant, AppOptions opt)
    {
        _qdrant = qdrant;
        _opt = opt;
    }

    public async Task<IReadOnlyList<SearchHit>> SearchAsync(
        float[] vector,
        int limit,
        CancellationToken cancellationToken = default)
    {
        var min = _opt.RetrievalMinScore;
        var hits = await _qdrant.SearchAsync(
            _opt.QdrantCollection,
            vector,
            limit,
            withPayload: true,
            minScore: min,
            cancellationToken: cancellationToken);

        if (hits.Count == 0) return Array.Empty<SearchHit>();
        var list = new List<SearchHit>(hits.Count);
        foreach (var p in hits)
        {
            var rec = QdrantScoredPointMapping.ToVendorRecord(p);
            if (rec is null) continue;
            list.Add(new SearchHit
            {
                Score = p.Score,
                Record = rec
            });
        }
        return list;
    }
}
