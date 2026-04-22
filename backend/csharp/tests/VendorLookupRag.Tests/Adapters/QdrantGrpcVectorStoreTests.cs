using Qdrant.Client.Grpc;
using VendorLookupRag.Adapters.Qdrant;
using VendorLookupRag.Configuration;
using VendorLookupRag.Tests.Fakes;

namespace VendorLookupRag.Tests.Adapters;

public class QdrantGrpcVectorStoreTests
{
    [Fact]
    public async Task SearchAsync_maps_hits_to_search_hits()
    {
        var sp = new ScoredPoint { Score = 0.88f };
        sp.Payload.Add("vendor_id", new Qdrant.Client.Grpc.Value { StringValue = "1" });
        sp.Payload.Add("legal_name", new Qdrant.Client.Grpc.Value { StringValue = "MapsCo" });

        var fake = new FakeQdrantPointSearch { Canned = new[] { sp } };
        var opt = new AppOptions
        {
            QdrantCollection = "vendor_master"
        };
        var store = new QdrantGrpcVectorStore(fake, opt);
        var hits = await store.SearchAsync([0.1f, 0.2f], 3);

        Assert.Single(fake.Calls);
        Assert.Equal("vendor_master", fake.Calls[0].Collection);
        Assert.Equal(2, fake.Calls[0].Vector.Length);
        Assert.Equal(3, fake.Calls[0].Limit);
        Assert.True(fake.Calls[0].WithPayload);
        Assert.Null(fake.Calls[0].MinScore);

        Assert.Single(hits);
        Assert.Equal(0.88, hits[0].Score, 3);
        Assert.Equal("MapsCo", hits[0].Record.LegalName);
    }

    [Fact]
    public async Task SearchAsync_passes_retrieval_min_score_to_qdrant()
    {
        var fake = new FakeQdrantPointSearch { Canned = Array.Empty<ScoredPoint>() };
        var opt = new AppOptions
        {
            QdrantCollection = "c",
            RetrievalMinScore = 0.6
        };
        var store = new QdrantGrpcVectorStore(fake, opt);
        _ = await store.SearchAsync([1f], 5);
        Assert.Equal(0.6, fake.Calls[0].MinScore);
    }
}
