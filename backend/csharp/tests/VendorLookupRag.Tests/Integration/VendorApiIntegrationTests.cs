using System.Net;
using System.Net.Http.Json;
using System.Text.Json.Serialization;
using VendorLookupRag.Models;
using VendorLookupRag.Tests.Support;

namespace VendorLookupRag.Tests.Integration;

/// <summary>End-to-end API over <see cref="TestServer"/>: health via stubbed HTTP, chat via <see cref="CannedToolLoopChatClient" /> + port fakes.</summary>
[Trait("Category", "integration")]
public class VendorApiIntegrationTests
{
    [Fact]
    public async Task V1_health_returns_service_map()
    {
        using var f = new VendorApiTestServer();
        f.Http.EnqueueJson200("""{"models":[]}""");
        f.Http.Enqueue(new HttpResponseMessage(HttpStatusCode.OK));
        var c = f.CreateClient();
        var r = await c.GetAsync("/v1/health");
        r.EnsureSuccessStatusCode();
        var j = await r.Content.ReadAsStringAsync();
        Assert.Contains("ollama", j);
        Assert.Contains("qdrant", j);
    }

    [Fact]
    public async Task V1_status_includes_model_names()
    {
        using var f = new VendorApiTestServer();
        f.Http.EnqueueJson200("""{"models":[]}""");
        f.Http.Enqueue(new HttpResponseMessage(HttpStatusCode.OK));
        var c = f.CreateClient();
        var r = await c.GetAsync("/v1/status");
        r.EnsureSuccessStatusCode();
        var o = await r.Content.ReadFromJsonAsync<StatusRow>();
        Assert.NotNull(o);
        Assert.Equal("gemma4:e4b", o!.ChatModel);
    }

    private sealed class StatusRow
    {
        [JsonPropertyName("chat_model")]
        public string? ChatModel { get; set; }
    }

    [Fact]
    public async Task V1_chat_runs_tool_loop_with_canned_ichatclient_and_fakes()
    {
        using var f = new VendorApiTestServer();
        f.VectorStore.SetDefaultHits(
        [
            new SearchHit
            {
                Score = 0.95,
                Record = new VendorRecord
                {
                    VendorId = "v1",
                    LegalName = "Acme Berlin GmbH"
                }
            }
        ]);
        var c = f.CreateClient();
        var chat = await c.PostAsJsonAsync("/v1/chat", new { message = "find acme" });
        chat.EnsureSuccessStatusCode();
        var body = await chat.Content.ReadAsStringAsync();
        Assert.Contains("display_markdown", body);
        Assert.Contains("Acme", body);
    }

    [Fact]
    public async Task V1_chat_trace_includes_last_tool_result_from_VendorLookupAgent()
    {
        using var f = new VendorApiTestServer();
        f.VectorStore.SetDefaultHits(
        [
            new SearchHit
            {
                Score = 0.95,
                Record = new VendorRecord { VendorId = "v1", LegalName = "Acme Berlin GmbH" }
            }
        ]);
        var c = f.CreateClient();
        var chat = await c.PostAsJsonAsync("/v1/chat", new { message = "find acme" });
        chat.EnsureSuccessStatusCode();
        var o = await chat.Content.ReadFromJsonAsync<TraceDto>();
        Assert.NotNull(o);
        Assert.NotNull(o!.Trace);
        Assert.Contains("last_tool_result", o.Trace, StringComparison.Ordinal);
    }

    private sealed class TraceDto
    {
        [JsonPropertyName("trace_text")]
        public string? Trace { get; set; }
    }
}
