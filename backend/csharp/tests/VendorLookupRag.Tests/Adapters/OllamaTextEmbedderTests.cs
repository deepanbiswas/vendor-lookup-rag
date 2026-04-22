using VendorLookupRag.Adapters.Ollama;
using VendorLookupRag.Configuration;
using VendorLookupRag.Tests.Support.Http;

namespace VendorLookupRag.Tests.Adapters;

/// <summary>Exercises the real <see cref="OllamaTextEmbedder" /> against canned HTTP (port fakes are in <see cref="Fakes.FakeTextEmbedder" />).</summary>
public class OllamaTextEmbedderTests
{
    [Fact]
    public async Task Embed_uses_post_api_embed()
    {
        var c = new HttpClient(new CannedOllamaEmbedResponseHandler()) { BaseAddress = new Uri("http://ollama/") };
        var o = new AppOptions { OllamaBaseUrl = "http://ollama" };
        var e = new OllamaTextEmbedder(c, o);
        var v = await e.EmbedAsync("  hello  ");
        Assert.Equal(3, v.Length);
        Assert.Equal(0.1f, v[0], 3);
    }
}
