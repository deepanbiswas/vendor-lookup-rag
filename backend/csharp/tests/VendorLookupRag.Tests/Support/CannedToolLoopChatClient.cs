using System.Runtime.CompilerServices;
using Microsoft.Extensions.AI;

namespace VendorLookupRag.Tests.Support;

/// <summary>Minimal <see cref="IChatClient" /> for integration tests: first call returns a <c>search_vendors</c> tool call, second returns <c>OK</c> (OllamaSharp uses native Ollama wire format, so we do not stub HTTP with OpenAI-style JSON).</summary>
public sealed class CannedToolLoopChatClient : IChatClient
{
    private int _call;

    public void Dispose()
    {
    }

    public object? GetService(Type serviceType, object? serviceKey = null) => null;

    public Task<ChatResponse> GetResponseAsync(
        IEnumerable<ChatMessage> messages,
        ChatOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        if (_call++ == 0)
        {
            return Task.FromResult(
                new ChatResponse(
                    new ChatMessage(
                        ChatRole.Assistant,
                    [
                        new FunctionCallContent(
                            "call1",
                            "search_vendors",
                            new Dictionary<string, object?> { ["user_query"] = "acme berlin" })
                    ])));
        }

        return Task.FromResult(new ChatResponse(new ChatMessage(ChatRole.Assistant, "OK")));
    }

    public async IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(
        IEnumerable<ChatMessage> messages,
        ChatOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await Task.CompletedTask;
        yield break;
    }
}
