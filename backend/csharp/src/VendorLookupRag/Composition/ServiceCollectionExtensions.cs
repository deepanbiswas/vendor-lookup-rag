using Microsoft.Extensions.AI;
using QdrantClient = Qdrant.Client.QdrantClient;
using VendorLookupRag.Adapters.Ollama;
using VendorLookupRag.Adapters.Qdrant;
using VendorLookupRag.Agents;
using VendorLookupRag.Configuration;
using VendorLookupRag.Ports;
using VendorLookupRag.Services;

namespace VendorLookupRag.Composition;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddVendorLookupRagCore(this IServiceCollection services, AppOptions options)
    {
        services.AddSingleton(options);
        // Health checks (Ollama /api/tags, Qdrant /readyz) use this client; do not share it with OllamaTextEmbedder,
        // which must set BaseAddress on a client that has not yet sent a request.
        services.AddSingleton(_ => new HttpClient { Timeout = TimeSpan.FromSeconds(300) });
        services.AddSingleton<IChatClient>(sp => OllamaChatClientFactory.Create(sp.GetRequiredService<AppOptions>()));
        services.AddSingleton<ITextEmbedder>(sp =>
        {
            var o = sp.GetRequiredService<AppOptions>();
            var http = new HttpClient
            {
                BaseAddress = new Uri(o.OllamaBaseUrl.TrimEnd('/') + "/"),
                Timeout = TimeSpan.FromSeconds(300)
            };
            return new OllamaTextEmbedder(http, o);
        });
        services.AddSingleton(sp =>
        {
            var o = sp.GetRequiredService<AppOptions>();
            return new QdrantClient(o.QdrantHost, o.QdrantGrpcPort, https: o.QdrantUseTls);
        });
        services.AddSingleton<IQdrantPointSearch, QdrantClientPointSearch>();
        services.AddSingleton<IVectorStore, QdrantGrpcVectorStore>();
        services.AddSingleton<VendorSearchService>();
        services.AddSingleton<IVendorSearchService>(sp => sp.GetRequiredService<VendorSearchService>());
        services.AddSingleton<VendorLookupAgent>();
        services.AddSingleton<ServiceHealthService>();
        return services;
    }
}
