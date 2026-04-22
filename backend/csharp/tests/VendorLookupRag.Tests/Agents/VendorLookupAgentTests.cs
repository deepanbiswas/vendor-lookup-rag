using Microsoft.Extensions.Logging.Abstractions;
using VendorLookupRag.Agents;
using VendorLookupRag.Configuration;
using VendorLookupRag.Models;
using VendorLookupRag.Services;
using VendorLookupRag.Tests.Fakes;
using VendorLookupRag.Tests.Support;

namespace VendorLookupRag.Tests.Agents;

public class VendorLookupAgentTests
{
    [Fact]
    public void AgentName_matches_framework_registration()
    {
        Assert.Equal("VendorLookupAgent", VendorLookupAgent.AgentName);
    }

    [Fact]
    public async Task RunChatTurnAsync_uses_tool_result_for_display_and_trace()
    {
        var fEmbed = new FakeTextEmbedder(new[] { 0.2f, 0.2f, 0.2f });
        var fStore = new FakeVectorStore();
        fStore.SetDefaultHits(
        [
            new SearchHit
            {
                Score = 0.95,
                Record = new VendorRecord { VendorId = "a", LegalName = "Contoso GmbH" }
            }
        ]);
        var opt = new AppOptions
        {
            QdrantCollection = "c",
            RetrievalTopK = 3
        };
        var search = new VendorSearchService(fEmbed, fStore, opt);
        var log = NullLogger<VendorLookupAgent>.Instance;
        var agent = new VendorLookupAgent(new CannedToolLoopChatClient(), search, log);
        var (display, trace) = await agent.RunChatTurnAsync("  find contoso  ");

        Assert.Contains("Contoso", display, StringComparison.Ordinal);
        Assert.Contains("last_tool_result", trace, StringComparison.Ordinal);
        Assert.Contains("assistant:", trace, StringComparison.Ordinal);
    }
}
