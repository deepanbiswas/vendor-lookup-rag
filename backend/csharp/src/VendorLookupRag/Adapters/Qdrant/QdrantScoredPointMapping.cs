using Qdrant.Client.Grpc;
using VendorLookupRag.Models;
using QValue = global::Qdrant.Client.Grpc.Value;

namespace VendorLookupRag.Adapters.Qdrant;

/// <summary>Maps a Qdrant gRPC <see cref="ScoredPoint" /> payload to <see cref="VendorRecord" />.</summary>
public static class QdrantScoredPointMapping
{
    public static VendorRecord? ToVendorRecord(ScoredPoint p)
    {
        if (p.Payload is null) return null;
        var m = p.Payload;
        return new VendorRecord
        {
            VendorId = S(m, "vendor_id"),
            LegalName = S(m, "legal_name"),
            City = SNull(m, "city"),
            PostalCode = SNull(m, "postal_code"),
            VatId = SNull(m, "vat_id"),
            Country = SNull(m, "country"),
            SecondaryName = SNull(m, "secondary_name"),
            CompanyCode = SNull(m, "company_code"),
            Address = SNull(m, "address"),
            State = SNull(m, "state"),
            DateFormat = SNull(m, "date_format"),
            EuMemberFlag = SNull(m, "eu_member_flag"),
            Extras = MapExtras(m)
        };
    }

    private static string S(IReadOnlyDictionary<string, QValue> m, string key) =>
        m.GetValueOrDefault(key) is { } v && v.KindCase == QValue.KindOneofCase.StringValue
            ? v.StringValue
            : "";

    private static string? SNull(IReadOnlyDictionary<string, QValue> m, string key)
    {
        if (!m.TryGetValue(key, out var v) || v.KindCase != QValue.KindOneofCase.StringValue) return null;
        return string.IsNullOrEmpty(v.StringValue) ? null : v.StringValue;
    }

    private static Dictionary<string, string> MapExtras(IReadOnlyDictionary<string, QValue> m)
    {
        if (!m.TryGetValue("extras", out var e) || e.KindCase != QValue.KindOneofCase.StructValue) return new();
        var s = e.StructValue;
        if (s.Fields is null) return new();
        var d = new Dictionary<string, string>();
        foreach (var (k, val) in s.Fields)
        {
            if (val.KindCase == QValue.KindOneofCase.StringValue) d[k] = val.StringValue;
        }
        return d;
    }
}
