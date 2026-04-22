using VendorLookupRag.Configuration;
using VendorLookupRag.Models;
using VendorLookupRag.Ports;

namespace VendorLookupRag.Services;

public sealed class VendorSearchService : IVendorSearchService
{
    private readonly ITextEmbedder _embedder;
    private readonly IVectorStore _store;
    private readonly AppOptions _opt;

    public VendorSearchService(ITextEmbedder embedder, IVectorStore store, AppOptions opt)
    {
        _embedder = embedder;
        _store = store;
        _opt = opt;
    }

    public async Task<object> SearchVendorsToolAsync(
        string userQuery,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var nq = TextNormalize.NormalizeText(userQuery);
            if (nq.Length == 0)
            {
                return new SearchVendorToolSuccess
                {
                    Kind = "none",
                    Message = "No matching vendors found. Flag for manual verification.",
                    Candidates = [],
                    RetrievalTopK = []
                };
            }

            var vector = await _embedder.EmbedAsync(nq, cancellationToken);
            var hits = (await _store.SearchAsync(vector, _opt.RetrievalTopK, cancellationToken))
                .ToList();
            if (_opt.RetrievalMinScore is { } min)
            {
                hits = hits.Where(h => h.Score >= min).ToList();
            }

            var match = MatchClassifier.ClassifyMatches(
                nq,
                hits,
                _opt.ScoreThresholdExact,
                _opt.ScoreThresholdPartial,
                _opt.ScoreTolerance);

            var topK = hits.Select(HitToCandidate).ToList();
            var kindStr = match.Kind switch
            {
                MatchKind.Exact => "exact",
                MatchKind.Partial => "partial",
                _ => "none"
            };
            return new SearchVendorToolSuccess
            {
                Kind = kindStr,
                Message = match.Message,
                Candidates = match.Hits.Select(HitToCandidate).ToList(),
                RetrievalTopK = topK
            };
        }
        catch (Exception ex)
        {
            return new SearchVendorToolError
            {
                Error = "retrieval_failed",
                Message = ex.Message,
                Detail = null
            };
        }
    }

    private static SearchVendorCandidate HitToCandidate(SearchHit h)
    {
        var r = h.Record;
        return new SearchVendorCandidate
        {
            Score = h.Score,
            VendorId = r.VendorId,
            LegalName = r.LegalName,
            SecondaryName = r.SecondaryName,
            CompanyCode = r.CompanyCode,
            City = r.City,
            VatId = r.VatId,
            Address = r.Address,
            State = r.State,
            PostalCode = r.PostalCode,
            Country = r.Country
        };
    }
}
