using System.Text.Json;
using System.Text.Json.Serialization;

namespace VendorLookupRag;

public static class JsonOptions
{
    public static readonly JsonSerializerOptions ForApi = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };
}
