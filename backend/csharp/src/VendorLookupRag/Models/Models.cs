using System.Text.Json;
using System.Text.Json.Serialization;

namespace VendorLookupRag.Models;

public sealed class VendorRecord
{
    [JsonPropertyName("vendor_id")]
    public string VendorId { get; set; } = "";
    [JsonPropertyName("legal_name")]
    public string LegalName { get; set; } = "";
    [JsonPropertyName("city")]
    public string? City { get; set; }
    [JsonPropertyName("postal_code")]
    public string? PostalCode { get; set; }
    [JsonPropertyName("vat_id")]
    public string? VatId { get; set; }
    [JsonPropertyName("country")]
    public string? Country { get; set; }
    [JsonPropertyName("secondary_name")]
    public string? SecondaryName { get; set; }
    [JsonPropertyName("company_code")]
    public string? CompanyCode { get; set; }
    [JsonPropertyName("address")]
    public string? Address { get; set; }
    [JsonPropertyName("state")]
    public string? State { get; set; }
    [JsonPropertyName("date_format")]
    public string? DateFormat { get; set; }
    [JsonPropertyName("eu_member_flag")]
    public string? EuMemberFlag { get; set; }
    [JsonPropertyName("extras")]
    public Dictionary<string, string> Extras { get; set; } = new();
}

public sealed class SearchHit
{
    public double Score { get; set; }
    public required VendorRecord Record { get; set; }
}

public sealed class SearchVendorCandidate
{
    [JsonPropertyName("score")]
    public double Score { get; set; }
    [JsonPropertyName("vendor_id")]
    public string VendorId { get; set; } = "";
    [JsonPropertyName("legal_name")]
    public string LegalName { get; set; } = "";
    [JsonPropertyName("secondary_name")]
    public string? SecondaryName { get; set; }
    [JsonPropertyName("company_code")]
    public string? CompanyCode { get; set; }
    [JsonPropertyName("city")]
    public string? City { get; set; }
    [JsonPropertyName("vat_id")]
    public string? VatId { get; set; }
    [JsonPropertyName("address")]
    public string? Address { get; set; }
    [JsonPropertyName("state")]
    public string? State { get; set; }
    [JsonPropertyName("postal_code")]
    public string? PostalCode { get; set; }
    [JsonPropertyName("country")]
    public string? Country { get; set; }
}

public sealed class SearchVendorToolSuccess
{
    [JsonPropertyName("ok")]
    public bool Ok { get; set; } = true;
    [JsonPropertyName("kind")]
    public string Kind { get; set; } = "";
    [JsonPropertyName("message")]
    public string Message { get; set; } = "";
    [JsonPropertyName("candidates")]
    public List<SearchVendorCandidate> Candidates { get; set; } = [];
    [JsonPropertyName("retrieval_top_k")]
    public List<SearchVendorCandidate> RetrievalTopK { get; set; } = [];
}

public sealed class SearchVendorToolError
{
    [JsonPropertyName("ok")]
    public bool Ok { get; set; } = false;
    [JsonPropertyName("error")]
    public string Error { get; set; } = "";
    [JsonPropertyName("message")]
    public string Message { get; set; } = "";
    [JsonPropertyName("detail")]
    public string? Detail { get; set; }
}
