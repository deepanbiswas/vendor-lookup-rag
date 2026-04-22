using VendorLookupRag.Models;
using VendorLookupRag.Ports;

namespace VendorLookupRag.Tests.Fakes;

/// <summary>Test double for <see cref="IVectorStore"/>, in the spirit of <c>backend/python/tests/fakes/vector_store.py</c>.</summary>
public sealed class FakeVectorStore : IVectorStore
{
    private IReadOnlyList<SearchHit> _defaultHits;
    private readonly Func<float[], int, IReadOnlyList<SearchHit>>? _onSearch;
    private readonly Exception? _searchSideEffect;

    public List<(float[] Vector, int Limit)> SearchCalls { get; } = new();

    public FakeVectorStore(
        IReadOnlyList<SearchHit>? searchHits = null,
        Func<float[], int, IReadOnlyList<SearchHit>>? onSearch = null,
        Exception? searchSideEffect = null)
    {
        _defaultHits = searchHits?.ToList() ?? new List<SearchHit>();
        _onSearch = onSearch;
        _searchSideEffect = searchSideEffect;
    }

    public void SetDefaultHits(IReadOnlyList<SearchHit> hits) => _defaultHits = hits.ToList();

    public Task<IReadOnlyList<SearchHit>> SearchAsync(
        float[] vector,
        int limit,
        CancellationToken cancellationToken = default)
    {
        SearchCalls.Add((vector, limit));
        if (_searchSideEffect is not null) throw _searchSideEffect;
        if (_onSearch is not null) return Task.FromResult(_onSearch(vector, limit));
        return Task.FromResult((IReadOnlyList<SearchHit>)_defaultHits.Take(limit).ToList());
    }
}
