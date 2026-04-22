using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.AspNetCore.TestHost;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using VendorLookupRag.Ports;
using VendorLookupRag.Tests.Fakes;

namespace VendorLookupRag.Tests.Support;

/// <summary>
/// Sets <c>VENDOR_LOOKUP_CSHARP_PORT=0</c>, registers <see cref="FakeTextEmbedder" /> and <see cref="FakeVectorStore" />
/// in place of the production adapters, and uses a <see cref="SequentialTestHttpMessageHandler" /> for <see cref="System.Net.Http.HttpClient" />
/// (<see cref="IChatClient" /> is a <see cref="CannedToolLoopChatClient" />; service health still uses the stubbed <see cref="System.Net.Http.HttpClient" />; embed/Qdrant HTTP are not used when ports are fakes).
/// </summary>
public sealed class VendorApiTestServer : WebApplicationFactory<Program>
{
    static VendorApiTestServer() =>
        Environment.SetEnvironmentVariable("VENDOR_LOOKUP_CSHARP_PORT", "0", EnvironmentVariableTarget.Process);

    public FakeTextEmbedder TextEmbedder { get; } = new();

    public FakeVectorStore VectorStore { get; } = new();

    public SequentialTestHttpMessageHandler Http { get; } = new();

    public VendorApiTestServer()
    {
    }

    protected override void ConfigureWebHost(IWebHostBuilder builder) =>
        builder
            .UseEnvironment(Environments.Development)
            .ConfigureTestServices(s =>
            {
                s.ReplaceService<ITextEmbedder>(TextEmbedder);
                s.ReplaceService<IVectorStore>(VectorStore);
                s.ReplaceHttpClient(Http);
                s.ReplaceService<IChatClient>(new CannedToolLoopChatClient());
            });
}
