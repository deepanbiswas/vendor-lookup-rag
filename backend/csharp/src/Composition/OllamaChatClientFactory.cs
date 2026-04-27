using Microsoft.Extensions.AI;
using OllamaSharp;
using VendorLookupRag.Configuration;

namespace VendorLookupRag.Composition;

/// <summary>Builds an <see cref="IChatClient" /> for Ollama via <see href="https://github.com/awaescher/OllamaSharp">OllamaSharp</see> (native API, not the OpenAI-compat <c>/v1</c> path).</summary>
public static class OllamaChatClientFactory
{
    public static IChatClient Create(AppOptions o) => Create(o, handler: null);

    /// <param name="handler">When set (e.g. integration tests), requests are sent through a stub <see cref="System.Net.Http.HttpMessageHandler" />.</param>
    public static IChatClient Create(AppOptions o, System.Net.Http.HttpMessageHandler? handler)
    {
        if (handler is not null)
        {
            var http = new System.Net.Http.HttpClient(handler) { BaseAddress = new Uri("https://test.invalid/") };
            return new OllamaApiClient(http, o.ChatModel);
        }

        var baseUri = new Uri(o.OllamaBaseUrl.TrimEnd('/') + "/");
        return new OllamaApiClient(baseUri, o.ChatModel);
    }
}
