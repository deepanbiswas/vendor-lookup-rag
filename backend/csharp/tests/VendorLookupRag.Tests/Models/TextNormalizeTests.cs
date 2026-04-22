using VendorLookupRag.Models;

namespace VendorLookupRag.Tests.Models;

public class TextNormalizeTests
{
    [Theory]
    [InlineData("  Acme Corp.  ", "acme corp")]
    [InlineData("Foo-Bar  Baz!", "foo bar baz")]
    [InlineData("VAT: DE1234567", "vat de1234567")]
    [InlineData("", "")]
    [InlineData("   ", "")]
    public void NormalizeText_Basic(string raw, string expected) =>
        Assert.Equal(expected, TextNormalize.NormalizeText(raw));

    [Theory]
    [InlineData("foo\t\n  bar", "foo bar")]
    [InlineData("line1\r\nline2", "line1 line2")]
    public void NormalizeText_Whitespace_Collapsed(string raw, string expected) =>
        Assert.Equal(expected, TextNormalize.NormalizeText(raw));

    [Fact]
    public void NormalizeText_NarrowNbsp() => Assert.Equal(
        "acme corp gmbh",
        TextNormalize.NormalizeText("acme\u00a0corp gmbh"));

    [Fact]
    public void NormalizeText_ZeroWidth() =>
        Assert.Equal("foo bar", TextNormalize.NormalizeText("foo\u200bbar"));

    [Theory]
    [InlineData("vendor_id_acme", "vendor id acme")]
    [InlineData("foo___bar", "foo bar")]
    [InlineData("a_b", "a b")]
    public void NormalizeText_Underscore(string raw, string expected) =>
        Assert.Equal(expected, TextNormalize.NormalizeText(raw));

    [Theory]
    [InlineData("ＡＣＭＥ　ＧｍｂＨ", "acme gmbh")]
    [InlineData("ＶＡＴ：　１２３", "vat 123")]
    public void NormalizeText_FullwidthNfkc(string raw, string expected) =>
        Assert.Equal(expected, TextNormalize.NormalizeText(raw));

    [Fact]
    public void NormalizedTokenSet_Split_And_Dedup() => Assert.Equal(
        new[] { "foo", "bar", "baz" }.ToHashSet(),
        TextNormalize.NormalizedTokenSet("Foo-Bar  Baz!"));

    [Fact]
    public void CompactForIdentifier() =>
        Assert.Equal("de123456", TextNormalize.CompactForIdentifierMatch("DE 123 456"));
}
