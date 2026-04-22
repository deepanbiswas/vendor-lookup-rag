using System.Text;
using System.Text.Json;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using VendorLookupRag.Models;
using VendorLookupRag.Ports;
using VendorLookupRag.Services;

namespace VendorLookupRag.Agents;

/// <summary>Vendor chat using Microsoft Agent Framework: Ollama via <see cref="IChatClient" /> and <c>search_vendors</c> as an <see cref="AIFunction" /> (see <c>AIFunctionFactory</c> in Microsoft.Extensions.AI).</summary>
public sealed class VendorLookupAgent
{
    public static string AgentName { get; } = "VendorLookupAgent";

    public const string SystemPrompt =
        """
        You help invoice processors verify vendors against a master list.
        Always call the search_vendors tool once with the user's vendor-related text (or a short paraphrase).
        Do not describe vendors, scores, or next steps in your assistant message — the application renders tool data.
        After the tool returns, reply with exactly the single word: OK.
        """;

    private readonly AIAgent _agent;
    private readonly IVendorSearchService _search;
    private readonly ILogger<VendorLookupAgent> _log;
    private string _lastToolResultJson = "";

    public VendorLookupAgent(
        IChatClient chat,
        IVendorSearchService search,
        ILogger<VendorLookupAgent> log)
    {
        _search = search;
        _log = log;
        var vendorSearchTool = CreateVendorSearchTool();
        _agent = chat.AsAIAgent(
            name: AgentName,
            instructions: SystemPrompt,
            tools: [vendorSearchTool]);
    }

    private AITool CreateVendorSearchTool() =>
        AIFunctionFactory.Create(
            async (string user_query, CancellationToken cancellationToken) =>
            {
                var r = await _search.SearchVendorsToolAsync(user_query, cancellationToken);
                _lastToolResultJson = r switch
                {
                    SearchVendorToolSuccess s => JsonSerializer.Serialize(s, JsonOptions.ForApi),
                    SearchVendorToolError e => JsonSerializer.Serialize(e, JsonOptions.ForApi),
                    _ => JsonSerializer.Serialize(r, JsonOptions.ForApi)
                };
                return _lastToolResultJson;
            },
            new AIFunctionFactoryOptions { Name = "search_vendors" });

    public async Task<(string DisplayMarkdown, string TraceText)> RunChatTurnAsync(
        string userMessage,
        CancellationToken cancellationToken = default)
    {
        _lastToolResultJson = "";
        _log.LogInformation("Chat turn: Microsoft.Agents.AI + OllamaSharp IChatClient");
        var response = await _agent.RunAsync(userMessage, cancellationToken: cancellationToken);
        var display = _lastToolResultJson.Length > 0
            ? ChatMarkdownFormatter.FormatFromToolResultJson(_lastToolResultJson)
            : (string.IsNullOrWhiteSpace(response.Text) ? "_No vendor search result in this turn._" : response.Text.Trim());
        var sb = new StringBuilder();
        if (response.Text is { Length: > 0 } t) sb.AppendLine("assistant: ").AppendLine(t);
        sb.Append("last_tool_result: ").Append(_lastToolResultJson);
        return (display, sb.ToString());
    }
}
