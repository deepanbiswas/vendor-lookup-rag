using VendorLookupRag.Ports;

namespace VendorLookupRag.Tests.Fakes;

/// <summary>Test double for <see cref="ITextEmbedder"/>, in the spirit of <c>backend/python/tests/fakes/embedding.py</c>.</summary>
public sealed class FakeTextEmbedder : ITextEmbedder
{
    private readonly float[]? _vector;
    private readonly Func<string, float[]>? _embedFn;
    private readonly Exception? _sideEffect;

    public List<string> Calls { get; } = new();

    public FakeTextEmbedder(
        float[]? vector = null,
        Func<string, float[]>? embedFn = null,
        Exception? sideEffect = null)
    {
        _vector = vector;
        _embedFn = embedFn;
        _sideEffect = sideEffect;
    }

    public Task<float[]> EmbedAsync(string text, CancellationToken cancellationToken = default)
    {
        Calls.Add(text);
        if (_sideEffect is not null) throw _sideEffect;
        if (_embedFn is not null) return Task.FromResult(_embedFn(text));
        if (_vector is { } a) return Task.FromResult((float[])a.Clone());
        return Task.FromResult(new[] { 1f });
    }
}
