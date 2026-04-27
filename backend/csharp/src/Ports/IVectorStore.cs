using VendorLookupRag.Models;

namespace VendorLookupRag.Ports;

public interface IVectorStore
{
    Task<IReadOnlyList<SearchHit>> SearchAsync(float[] vector, int limit, CancellationToken cancellationToken = default);
}
