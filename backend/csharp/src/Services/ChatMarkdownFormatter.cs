using System.Text.Json;
using VendorLookupRag.Models;

namespace VendorLookupRag.Services;

/// <summary>Ports <c>ui/chat_display</c> formatting (tool-first display).</summary>
public static class ChatMarkdownFormatter
{
    public static string FormatFromToolResultJson(string toolContentJson)
    {
        using var doc = JsonDocument.Parse(toolContentJson);
        var root = doc.RootElement;
        if (root.TryGetProperty("ok", out var ok) && ok.ValueKind == JsonValueKind.False)
        {
            var msg = root.TryGetProperty("message", out var m) ? m.GetString() ?? "error" : "error";
            return $"**Vendor search failed:** {msg}";
        }
        var s = JsonSerializer.Deserialize<SearchVendorToolSuccess>(toolContentJson, JsonOptions.ForApi);
        if (s is not null) return FormatSearchToolMarkdown(s);
        return "_No vendor search result in this turn._";
    }

    public static string FormatSearchToolMarkdown(SearchVendorToolSuccess s)
    {
        if (s.Candidates.Count == 0)
        {
            return "_No vendor met the partial similarity threshold. " +
                   "See **Agent run details** for full top‑k retrieval scores._";
        }
        var blocks = new List<string>();
        for (var i = 0; i < s.Candidates.Count; i++)
        {
            var c = s.Candidates[i];
            blocks.Add($"### {i + 1}. {c.LegalName}\n\n{FormatCandidateBlock(c)}");
        }
        return string.Join("\n\n---\n\n", blocks);
    }

    private static string FormatCandidateBlock(SearchVendorCandidate c)
    {
        var lines = new List<string> { $"**Confidence (cosine):** {c.Score:F6}" };
        void Add(string label, string? v)
        {
            if (string.IsNullOrWhiteSpace(v)) return;
            lines.Add($"**{label}:** {v}");
        }
        Add("Vendor ID", c.VendorId);
        Add("Legal name", c.LegalName);
        Add("Secondary name", c.SecondaryName);
        Add("Company code", c.CompanyCode);
        Add("Address", c.Address);
        Add("City", c.City);
        Add("State", c.State);
        Add("Postal code", c.PostalCode);
        Add("Country", c.Country);
        Add("VAT / tax ID", c.VatId);
        return string.Join("\n\n", lines);
    }
}
