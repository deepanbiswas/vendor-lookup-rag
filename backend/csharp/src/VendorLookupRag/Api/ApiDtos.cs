using System.Text.Json.Serialization;

namespace VendorLookupRag.Api;

public sealed class ServiceHealthDto
{
    [JsonPropertyName("ok")]
    public bool Ok { get; init; }
    [JsonPropertyName("detail")]
    public string Detail { get; init; } = "";
}

public sealed class HealthResponse
{
    [JsonPropertyName("services")]
    public required Dictionary<string, ServiceHealthDto> Services { get; init; }
}

public sealed class StatusResponse
{
    [JsonPropertyName("services")]
    public required Dictionary<string, ServiceHealthDto> Services { get; init; }
    [JsonPropertyName("chat_model")]
    public required string ChatModel { get; init; }
    [JsonPropertyName("embedding_model")]
    public required string EmbeddingModel { get; init; }
    [JsonPropertyName("score_threshold_exact")]
    public required double ScoreThresholdExact { get; init; }
    [JsonPropertyName("score_threshold_partial")]
    public required double ScoreThresholdPartial { get; init; }
    [JsonPropertyName("score_tolerance")]
    public required double ScoreTolerance { get; init; }
}

public sealed class ChatRequest
{
    [JsonPropertyName("message")]
    public required string Message { get; init; }
}

public sealed class ChatResponse
{
    [JsonPropertyName("display_markdown")]
    public required string DisplayMarkdown { get; init; }
    [JsonPropertyName("trace_text")]
    public required string TraceText { get; init; }
}
