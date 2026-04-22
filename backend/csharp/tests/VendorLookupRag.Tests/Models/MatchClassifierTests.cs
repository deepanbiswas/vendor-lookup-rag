using VendorLookupRag.Models;
using VRec = VendorLookupRag.Models.VendorRecord;
using SHit = VendorLookupRag.Models.SearchHit;

namespace VendorLookupRag.Tests.Models;

public class MatchClassifierTests
{
    private static string Nq(string s) => TextNormalize.NormalizeText(s);

    private static SHit H(
        double score,
        string vid = "v1",
        string name = "Acme GmbH",
        string? vat = "DE123",
        string? secondary = null,
        string? cc = null) =>
        new()
        {
            Score = score,
            Record = new VRec
            {
                VendorId = vid,
                LegalName = name,
                VatId = vat,
                SecondaryName = secondary,
                CompanyCode = cc
            }
        };

    [Fact]
    public void No_hits() =>
        Assert.Equal(MatchKind.None, MatchClassifier.ClassifyMatches(Nq("x"), Array.Empty<SHit>(), 0.9, 0.5).Kind);

    [Fact]
    public void Exact_name_overlap() =>
        Assert.Equal(
            MatchKind.Exact,
            MatchClassifier
                .ClassifyMatches(
                    Nq("acme berlin gmbh"),
                    [H(0.95, name: "Acme Berlin GmbH")], 0.92, 0.55)
                .Kind);

    [Fact]
    public void Exact_via_VAT() =>
        Assert.Equal(
            MatchKind.Exact,
            MatchClassifier.ClassifyMatches(Nq("de999 something"), [H(0.93, vat: "DE999")], 0.92, 0.55)
                .Kind);

    [Fact]
    public void High_cosine_no_overlap_is_partial() =>
        Assert.Equal(
            MatchKind.Partial,
            MatchClassifier.ClassifyMatches(
                Nq("completely different words"),
                [H(0.97)], 0.92, 0.55)
                .Kind);

    [Fact]
    public void None_low_score() =>
        Assert.Equal(
            MatchKind.None,
            MatchClassifier.ClassifyMatches(Nq("x"), [H(0.3)], 0.92, 0.55)
                .Kind);

    [Fact]
    public void Tolerance_allows_slightly_lower_partial() =>
        Assert.Equal(
            MatchKind.Partial,
            MatchClassifier.ClassifyMatches(
                Nq("unrelated"),
                [H(0.68, name: "Borderline Corp")],
                0.92,
                0.7,
                0.05)
                .Kind);

    [Fact]
    public void Effective_floors_clamp()
    {
        var (fE, fP) = MatchClassifier.EffectiveFloors(0.92, 0.7, 0.05);
        Assert.Equal(0.87, fE, 2);
        Assert.Equal(0.65, fP, 2);
        (fE, fP) = MatchClassifier.EffectiveFloors(0.1, 0.1, 0.2);
        Assert.Equal(0.0, fE, 2);
        Assert.Equal(0.0, fP, 2);
    }
}
