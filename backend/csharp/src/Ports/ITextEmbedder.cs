namespace VendorLookupRag.Ports;

public interface ITextEmbedder
{
    Task<float[]> EmbedAsync(string text, CancellationToken cancellationToken = default);
}
