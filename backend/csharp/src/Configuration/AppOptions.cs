namespace VendorLookupRag.Configuration;

/// <summary>Runtime settings aligned with the Python <c>Settings</c> and environment variables.</summary>
public class AppOptions
{
    public const string SectionName = "VendorLookup";

    public string OllamaBaseUrl { get; set; } = "http://localhost:11434";

    /// <summary>HTTP base URL for Qdrant REST (e.g. <c>/readyz</c> in <see cref="Services.ServiceHealthService" />). The port in this URL is the REST port only, not the gRPC port.</summary>
    public string QdrantUrl { get; set; } = "http://localhost:6333";

    /// <summary>
    /// gRPC port for <see href="https://github.com/qdrant/qdrant-dotnet">Qdrant.Client</see> (<see cref="Qdrant.Client.QdrantClient" /> in DI).
    /// This is <b>independent</b> of the port in <see cref="QdrantUrl" />: vector search always uses <see cref="QdrantHost" /> + this port. Standard is REST 6333, gRPC 6334. On the host, if REST is published as 6335, set gRPC to the matching mapping (e.g. 6336) via <c>QDRANT_GRPC_PORT</c>.
    /// </summary>
    public int QdrantGrpcPort { get; set; } = 6334;
    public string QdrantCollection { get; set; } = "vendor_master";
    public string ChatModel { get; set; } = "gemma4:e4b";
    public string EmbeddingModel { get; set; } = "nomic-embed-text";
    public int EmbeddingVectorSize { get; set; } = 768;
    public int RetrievalTopK { get; set; } = 5;
    public double ScoreThresholdExact { get; set; } = 0.92;
    public double ScoreThresholdPartial { get; set; } = 0.55;
    public double ScoreTolerance { get; set; } = 0.0;
    public double? RetrievalMinScore { get; set; }
    public int ApiPort { get; set; } = 8001;

    /// <summary>When true, <c>POST /v1/chat</c> problem responses include full exception text (set in Docker e.g. via <c>VENDOR_LOOKUP_EXPOSE_ERROR_DETAILS</c> for local debugging; avoid in public deployments).</summary>
    public bool ExposeErrorDetails { get; set; }

    public string QdrantHost
    {
        get
        {
            var u = new Uri(QdrantUrl, UriKind.Absolute);
            return u.Host;
        }
    }

    /// <summary>True when <see cref="QdrantUrl" /> uses <c>https</c> (for gRPC client TLS in <c>Qdrant.Client</c>).</summary>
    public bool QdrantUseTls
    {
        get
        {
            var u = new Uri(QdrantUrl, UriKind.Absolute);
            return u.Scheme == Uri.UriSchemeHttps;
        }
    }
}
