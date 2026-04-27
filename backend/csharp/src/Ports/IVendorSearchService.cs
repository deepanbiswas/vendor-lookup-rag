namespace VendorLookupRag.Ports;

/// <summary>Application use case: run the <c>search_vendors</c> tool pipeline (normalize → embed → vector search → classify).</summary>
public interface IVendorSearchService
{
    Task<object> SearchVendorsToolAsync(string userQuery, CancellationToken cancellationToken = default);
}
