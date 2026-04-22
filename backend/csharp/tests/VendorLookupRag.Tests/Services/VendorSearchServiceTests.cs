using VendorLookupRag.Configuration;
using VendorLookupRag.Models;
using VendorLookupRag.Services;
using VendorLookupRag.Tests.Fakes;
using VRec = VendorLookupRag.Models.VendorRecord;

namespace VendorLookupRag.Tests.Services;

public class VendorSearchServiceTests
{
    [Fact]
    public async Task Search_returns_structured_ok()
    {
        var o = new AppOptions { ScoreThresholdExact = 0.92, ScoreThresholdPartial = 0.55, RetrievalTopK = 3 };
        var s = new VendorSearchService(
            new FakeTextEmbedder(vector: [1f, 0f, 0f]),
            new FakeVectorStore(
            [
                new SearchHit
                {
                    Score = 0.95,
                    Record = new VRec
                    {
                        VendorId = "a",
                        LegalName = "Acme Berlin GmbH"
                    }
                }
            ]),
            o);
        var r = await s.SearchVendorsToolAsync("acme berlin gmbh");
        var success = Assert.IsType<SearchVendorToolSuccess>(r);
        Assert.True(success.Ok);
        Assert.Equal("exact", success.Kind);
    }
}
