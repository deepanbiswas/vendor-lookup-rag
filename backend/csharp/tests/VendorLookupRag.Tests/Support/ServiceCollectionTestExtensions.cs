using System.Net;
using System.Net.Http.Headers;
using Microsoft.Extensions.DependencyInjection;

namespace VendorLookupRag.Tests.Support;

/// <summary>Replaces the last-registered <see cref="HttpClient" /> in DI (used in <c>WebApplicationFactory.ConfigureTestServices</c>).</summary>
public static class ServiceCollectionTestExtensions
{
    /// <summary>Removes prior registration(s) of <typeparamref name="TService" /> and registers <paramref name="instance" /> (e.g. port fakes).</summary>
    public static IServiceCollection ReplaceService<TService>(this IServiceCollection services, TService instance)
        where TService : class
    {
        foreach (var d in services.Where(s => s.ServiceType == typeof(TService)).ToList()) services.Remove(d);
        services.AddSingleton(instance);
        return services;
    }

    public static IServiceCollection ReplaceService<TService>(
        this IServiceCollection services,
        Func<IServiceProvider, TService> factory)
        where TService : class
    {
        foreach (var d in services.Where(s => s.ServiceType == typeof(TService)).ToList()) services.Remove(d);
        services.AddSingleton(factory);
        return services;
    }

    public static IServiceCollection ReplaceHttpClient(
        this IServiceCollection services,
        HttpMessageHandler handler)
    {
        foreach (var d in services.Where(s => s.ServiceType == typeof(HttpClient)).ToList()) services.Remove(d);
        var client = new HttpClient(handler) { BaseAddress = new Uri("https://test.invalid/") };
        client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
        services.AddSingleton(client);
        return services;
    }

    public static HttpResponseMessage OkJson(string json) =>
        new()
        {
            StatusCode = HttpStatusCode.OK,
            Content = new StringContent(json, System.Text.Encoding.UTF8, "application/json")
        };
}
