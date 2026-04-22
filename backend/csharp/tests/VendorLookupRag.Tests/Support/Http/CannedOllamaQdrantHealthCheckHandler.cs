using System.Net;
using System.Text;
using VendorLookupRag.Services;

namespace VendorLookupRag.Tests.Support.Http;

/// <summary>HTTP responses for <see cref="ServiceHealthService" />: Ollama <c>api/tags</c> and Qdrant <c>readyz</c>.</summary>
public sealed class CannedOllamaQdrantHealthCheckHandler : HttpMessageHandler
{
    public int Calls { get; private set; }

    protected override Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken)
    {
        Calls++;
        if (request.RequestUri!.AbsolutePath.Contains("tags", StringComparison.Ordinal)) return Task.FromResult(Ok("{\"models\":[]}"));
        if (request.RequestUri.AbsolutePath.Contains("readyz", StringComparison.Ordinal)) return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK));
        return Task.FromResult(new HttpResponseMessage(HttpStatusCode.NotFound));
    }

    private static HttpResponseMessage Ok(string json) => new() { StatusCode = HttpStatusCode.OK, Content = new StringContent(json, Encoding.UTF8, "application/json") };
}
