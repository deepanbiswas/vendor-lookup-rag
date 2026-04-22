using System.Text.Json;
using VendorLookupRag.Models;
using VendorLookupRag.Services;

namespace VendorLookupRag.Tests.Services;

public class ChatMarkdownFormatterTests
{
    [Fact]
    public void Formats_error_tool_json()
    {
        var s = """
            {"ok":false,"error":"retrieval_failed","message":"boom","detail":null}
            """;
        var md = ChatMarkdownFormatter.FormatFromToolResultJson(s);
        Assert.Contains("Vendor search failed", md);
        Assert.Contains("boom", md);
    }

    [Fact]
    public void Formats_success_with_candidates()
    {
        var ok = new SearchVendorToolSuccess
        {
            Ok = true,
            Kind = "partial",
            Message = "m",
            Candidates = [
                new SearchVendorCandidate
                {
                    Score = 0.88, VendorId = "1", LegalName = "X GmbH", City = "Berlin"
                }
            ],
            RetrievalTopK = []
        };
        var json = JsonSerializer.Serialize(ok, JsonOptions.ForApi);
        var md = ChatMarkdownFormatter.FormatFromToolResultJson(json);
        Assert.Contains("X GmbH", md);
        Assert.Contains("0.880000", md);
    }
}
