using VendorLookupRag.Configuration;
using VendorLookupRag.Services;
using VendorLookupRag.Tests.Support.Http;

namespace VendorLookupRag.Tests.Services;

public class ServiceHealthServiceTests
{
    [Fact]
    public async Task Ollama_and_qdrant_report_ok()
    {
        var h = new CannedOllamaQdrantHealthCheckHandler();
        var c = new HttpClient(h) { BaseAddress = new Uri("https://t/") };
        var svc = new ServiceHealthService(c);
        var d = await svc.GetServicesAsync(new AppOptions
        {
            OllamaBaseUrl = "http://localhost:11434",
            QdrantUrl = "http://localhost:6333"
        });
        Assert.True(d["ollama"].Ok);
        Assert.True(d["qdrant"].Ok);
        Assert.True(h.Calls >= 2, "one HTTP call per health check");
    }
}
