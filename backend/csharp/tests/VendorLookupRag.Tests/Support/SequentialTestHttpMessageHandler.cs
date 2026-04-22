using System.Collections.Concurrent;
using System.Net;

namespace VendorLookupRag.Tests.Support;

/// <summary>Dequeues a response per <see cref="HttpClient" /> call (same order the app issues requests).</summary>
public sealed class SequentialTestHttpMessageHandler : HttpMessageHandler
{
    public ConcurrentQueue<Task<HttpResponseMessage>> Responses { get; } = new();
    public List<string> RequestUris { get; } = [];

    public void EnqueueJson200(string json) => Responses.Enqueue(
        Task.FromResult(ServiceCollectionTestExtensions.OkJson(json)));

    public void Enqueue(HttpResponseMessage response) => Responses.Enqueue(
        Task.FromResult(response));

    protected override Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken)
    {
        if (request.RequestUri is { } u) RequestUris.Add(u.ToString());
        if (Responses.TryDequeue(out var t) && t is { }) return t!;

        return Task.FromResult(
            new HttpResponseMessage(HttpStatusCode.NotFound)
            {
                Content = new StringContent("{\"unmocked\":\"" + request.RequestUri + "\"}"),
            });
    }
}
