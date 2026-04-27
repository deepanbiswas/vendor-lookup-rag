using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace VendorLookupRag.Models;

/// <summary>Ports Python <c>normalization.text</c> behavior (NFKC, zero-width, punctuation → space).</summary>
public static class TextNormalize
{
    private static readonly Regex ZeroWidth = new(
        "[\u200b\u200c\u200d\u2060\ufeff]",
        RegexOptions.Compiled);

    // Match Python: _+ (each underscore run, including a single _, becomes a space).
    private static readonly Regex UnderscoreRuns = new("_+", RegexOptions.Compiled);
    private static readonly Regex WhitespaceRuns = new(@"\s+", RegexOptions.Compiled);

    // Non "word" → space: Python \W in UNICODE mode. Approximate: not letter, number, mark, or connector.
    private static readonly Regex NonWord = new(
        @"[^\p{L}\p{M}\p{N}\p{Pc}]",
        RegexOptions.Compiled);

    public static string NormalizeText(string? text)
    {
        if (string.IsNullOrEmpty(text)) return "";
        var t = text.Normalize(NormalizationForm.FormKC);
        t = ZeroWidth.Replace(t, " ");
        t = t.ToLowerInvariant().Trim();
        t = UnderscoreRuns.Replace(t, " ");
        t = NonWord.Replace(t, " ");
        t = WhitespaceRuns.Replace(t, " ");
        return t.Trim();
    }

    public static HashSet<string> NormalizedTokenSet(string text)
    {
        var n = NormalizeText(text);
        if (n.Length == 0) return new HashSet<string>(StringComparer.Ordinal);
        return n.Split(' ', StringSplitOptions.RemoveEmptyEntries)
            .ToHashSet(StringComparer.Ordinal);
    }

    public static string CompactForIdentifierMatch(string? text) =>
        NormalizeText(text).Replace(" ", "", StringComparison.Ordinal);
}
