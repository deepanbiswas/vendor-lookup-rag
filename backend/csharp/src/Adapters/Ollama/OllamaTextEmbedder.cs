using OllamaSharp;
using OllamaSharp.Models;
using VendorLookupRag.Configuration;
using VendorLookupRag.Ports;

namespace VendorLookupRag.Adapters.Ollama;

public sealed class OllamaTextEmbedder : ITextEmbedder
{
    private readonly OllamaApiClient _ollama;
    private readonly AppOptions _opt;

    public OllamaTextEmbedder(HttpClient http, AppOptions opt)
    {
        _opt = opt;
        // Do not set BaseAddress after the client has been used; prefer a dedicated HttpClient (see DI) or set only when null.
        if (http.BaseAddress is null)
        {
            http.BaseAddress = new Uri(opt.OllamaBaseUrl.TrimEnd('/') + "/");
        }
        _ollama = new OllamaApiClient(http, opt.EmbeddingModel);
    }

    public async Task<float[]> EmbedAsync(string text, CancellationToken cancellationToken = default)
    {
        var t = text.Trim();
        if (t.Length == 0) throw new ArgumentException("embed requires non-empty text");

        var request = new EmbedRequest
        {
            Model = _opt.EmbeddingModel,
            Input = [t]
        };
        var response = await _ollama.EmbedAsync(request, cancellationToken);
        if (response?.Embeddings is not { Count: > 0 })
        {
            throw new InvalidOperationException("Ollama /api/embed: empty vector");
        }
        return response.Embeddings[0];
    }
}
