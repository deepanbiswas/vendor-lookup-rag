namespace VendorLookupRag.Models;

public enum MatchKind
{
    Exact,
    Partial,
    None
}

public sealed class MatchResult
{
    public MatchKind Kind { get; init; }
    public required List<SearchHit> Hits { get; init; }
    public required string Message { get; init; }
}

/// <summary>Ports <c>matching.classify</c> (same thresholds and overlap rules as Python).</summary>
public static class MatchClassifier
{
    public static MatchResult ClassifyMatches(
        string normalizedQuery,
        IReadOnlyList<SearchHit> hits,
        double scoreExact,
        double scorePartial,
        double scoreTolerance = 0.0)
    {
        if (hits.Count == 0)
        {
            return new MatchResult
            {
                Kind = MatchKind.None,
                Hits = [],
                Message = "No matching vendors found. Flag for manual verification."
            };
        }

        var (fe, fp) = EffectiveFloors(scoreExact, scorePartial, scoreTolerance);
        var top = hits[0];
        var qCompact = QueryCompact(normalizedQuery);
        var idHit = IdentifierInQuery(top.Record, qCompact);
        var nameOverlap = NameOverlap(normalizedQuery, top.Record);
        var atPartial = HitsMeetingScoreFloor(hits, fp);

        if (top.Score >= fe && (idHit || nameOverlap))
        {
            return new MatchResult
            {
                Kind = MatchKind.Exact,
                Hits = atPartial,
                Message = "Exact match — displaying vendor details."
            };
        }

        if (top.Score >= fp)
        {
            return new MatchResult
            {
                Kind = MatchKind.Partial,
                Hits = atPartial,
                Message = "Partial match — review suggested candidates below."
            };
        }

        return new MatchResult
        {
            Kind = MatchKind.None,
            Hits = [],
            Message = "No confident match. Flag for manual verification."
        };
    }

    /// <summary>Exposed for unit tests; mirrors <c>matching.classify._effective_floors</c> in Python.</summary>
    public static (double Fe, double Fp) EffectiveFloors(
        double scoreExact,
        double scorePartial,
        double scoreTolerance) =>
        (Math.Min(1.0, Math.Max(0, scoreExact - scoreTolerance)),
            Math.Min(1.0, Math.Max(0, scorePartial - scoreTolerance)));

    private static string QueryCompact(string normalizedQuery) =>
        normalizedQuery.Replace(" ", "", StringComparison.Ordinal).ToLowerInvariant();

    private static HashSet<string> VendorTokensForOverlap(VendorRecord r)
    {
        var t = new HashSet<string>(StringComparer.Ordinal);
        void Add(string? s)
        {
            if (string.IsNullOrEmpty(s)) return;
            foreach (var x in TextNormalize.NormalizedTokenSet(s!))
                t.Add(x);
        }
        Add(r.LegalName);
        Add(r.SecondaryName);
        Add(r.CompanyCode);
        return t;
    }

    private static bool NameOverlap(string normalizedQuery, VendorRecord r)
    {
        var qTokens = TextNormalize.NormalizedTokenSet(normalizedQuery);
        if (qTokens.Count == 0) return false;
        var vTokens = VendorTokensForOverlap(r);
        if (qTokens.Count == 1) return vTokens.Overlaps(qTokens);
        var inter = new HashSet<string>(qTokens);
        inter.IntersectWith(vTokens);
        return inter.Count >= 2;
    }

    private static bool IdentifierInQuery(VendorRecord r, string qCompact)
    {
        var vat = TextNormalize.CompactForIdentifierMatch(r.VatId);
        if (vat.Length > 0 && qCompact.Contains(vat, StringComparison.Ordinal)) return true;
        var cc = TextNormalize.CompactForIdentifierMatch(r.CompanyCode);
        return cc.Length >= 2 && qCompact.Contains(cc, StringComparison.Ordinal);
    }

    private static List<SearchHit> HitsMeetingScoreFloor(IReadOnlyList<SearchHit> hits, double minScore) =>
        hits.Where(h => h.Score >= minScore).ToList();
}
