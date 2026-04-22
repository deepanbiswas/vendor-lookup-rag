using VendorLookupRag.Configuration;

namespace VendorLookupRag.Services;

public sealed class ServiceHealthService
{
    private readonly HttpClient _http;

    public ServiceHealthService(HttpClient http) => _http = http;

    public async Task<Dictionary<string, (bool Ok, string Detail)>> GetServicesAsync(
        AppOptions options,
        CancellationToken cancellationToken = default)
    {
        return new Dictionary<string, (bool, string)>
        {
            ["ollama"] = await CheckOllamaAsync(options.OllamaBaseUrl, cancellationToken),
            ["qdrant"] = await CheckQdrantAsync(options.QdrantUrl, cancellationToken)
        };
    }

    private async Task<(bool, string)> CheckOllamaAsync(string baseUrl, CancellationToken cancellationToken)
    {
        try
        {
            var r = await _http.GetAsync($"{baseUrl.TrimEnd('/')}/api/tags", cancellationToken);
            r.EnsureSuccessStatusCode();
            return (true, "reachable");
        }
        catch (Exception e)
        {
            return (false, e.Message[..Math.Min(200, e.Message.Length)]);
        }
    }

    private async Task<(bool, string)> CheckQdrantAsync(string baseUrl, CancellationToken cancellationToken)
    {
        try
        {
            var r = await _http.GetAsync($"{baseUrl.TrimEnd('/')}/readyz", cancellationToken);
            if ((int)r.StatusCode == 200) return (true, "ready");
            return (false, $"HTTP {(int)r.StatusCode}");
        }
        catch (Exception e)
        {
            return (false, e.Message[..Math.Min(200, e.Message.Length)]);
        }
    }
}
