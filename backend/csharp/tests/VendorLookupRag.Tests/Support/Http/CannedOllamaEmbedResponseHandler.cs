using System.Net;
using System.Text;
using System.Text.Json;

namespace VendorLookupRag.Tests.Support.Http;

/// <summary>HTTP test double for <b>Ollama <c>/api/embed</c> JSON</b> (used by <c>OllamaTextEmbedder</c> unit tests, not a port fake).</summary>
public sealed class CannedOllamaEmbedResponseHandler : HttpMessageHandler
{
    protected override Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken)
    {
        if (request.RequestUri?.ToString().Contains("embed", StringComparison.Ordinal) == true)
        {
            var body = new { embeddings = new[] { new[] { 0.1, 0.2, 0.3 } } };
            return Task.FromResult(
                new HttpResponseMessage(HttpStatusCode.OK)
                {
                    Content = new StringContent(JsonSerializer.Serialize(body), Encoding.UTF8, "application/json")
                });
        }

        return Task.FromResult(new HttpResponseMessage(HttpStatusCode.NotFound));
    }
}
