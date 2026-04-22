using VendorLookupRag.Configuration;

namespace VendorLookupRag.Composition;

public static class AppOptionsFactory
{
    public static AppOptions FromEnvironment()
    {
        var o = new AppOptions();
        o.OllamaBaseUrl = Env("OLLAMA_BASE_URL", o.OllamaBaseUrl);
        o.QdrantUrl = Env("QDRANT_URL", o.QdrantUrl);
        if (int.TryParse(Env("QDRANT_GRPC_PORT", null), out var qg)) o.QdrantGrpcPort = qg;
        o.QdrantCollection = Env("QDRANT_COLLECTION", o.QdrantCollection);
        o.ChatModel = Env("CHAT_MODEL", o.ChatModel);
        o.EmbeddingModel = Env("EMBEDDING_MODEL", o.EmbeddingModel);
        if (int.TryParse(Env("EMBEDDING_VECTOR_SIZE", null), out var evs)) o.EmbeddingVectorSize = evs;
        if (int.TryParse(Env("RETRIEVAL_TOP_K", null), out var tk)) o.RetrievalTopK = tk;
        if (double.TryParse(Env("SCORE_THRESHOLD_EXACT", null), out var se)) o.ScoreThresholdExact = se;
        if (double.TryParse(Env("SCORE_THRESHOLD_PARTIAL", null), out var sp)) o.ScoreThresholdPartial = sp;
        if (double.TryParse(Env("SCORE_TOLERANCE", null), out var st)) o.ScoreTolerance = st;
        if (double.TryParse(Env("RETRIEVAL_MIN_SCORE", null), out var rms)) o.RetrievalMinScore = rms;
        if (int.TryParse(Env("VENDOR_LOOKUP_CSHARP_PORT", null), out var p)) o.ApiPort = p;
        if (string.Equals(Env("VENDOR_LOOKUP_EXPOSE_ERROR_DETAILS", null), "true", StringComparison.OrdinalIgnoreCase)
            || string.Equals(Env("VENDOR_LOOKUP_EXPOSE_ERROR_DETAILS", null), "1", StringComparison.OrdinalIgnoreCase))
        {
            o.ExposeErrorDetails = true;
        }
        o.OllamaBaseUrl = o.OllamaBaseUrl.Trim().TrimEnd('/');
        o.QdrantUrl = o.QdrantUrl.Trim().TrimEnd('/');
        return o;
    }

    private static string Env(string name, string? d) => Environment.GetEnvironmentVariable(name) ?? d ?? "";
}
