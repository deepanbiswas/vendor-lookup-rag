using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using VendorLookupRag.Api;
using VendorLookupRag.Agents;
using VendorLookupRag.Configuration;
using VendorLookupRag.Services;

namespace VendorLookupRag;

public static class VendorApiRouteExtensions
{
    public static WebApplication MapVendorApi(this WebApplication app)
    {
        var api = app.MapGroup("/v1");
        api.MapGet("/health", GetHealth);
        api.MapGet("/status", GetStatus);
        api.MapPost("/chat", PostChat);
        return app;
    }

    private static async Task<Results<Ok<HealthResponse>, ProblemHttpResult>> GetHealth(
        [FromServices] ServiceHealthService health,
        [FromServices] AppOptions options,
        [FromServices] ILogger<Program> log,
        CancellationToken cancellationToken)
    {
        try
        {
            var raw = await health.GetServicesAsync(options, cancellationToken);
            return TypedResults.Ok(new HealthResponse
            {
                Services = raw.ToDictionary(
                    kv => kv.Key,
                    kv => new ServiceHealthDto
                    {
                        Ok = kv.Value.Ok,
                        Detail = kv.Value.Detail
                    })
            });
        }
        catch (Exception e)
        {
            log.LogError(e, "GET /v1/health: failed");
            return TypedResults.Problem(detail: e.Message, statusCode: 502);
        }
    }

    private static async Task<Results<Ok<StatusResponse>, ProblemHttpResult>> GetStatus(
        [FromServices] ServiceHealthService health,
        [FromServices] AppOptions options,
        [FromServices] ILogger<Program> log,
        CancellationToken cancellationToken)
    {
        try
        {
            var raw = await health.GetServicesAsync(options, cancellationToken);
            return TypedResults.Ok(new StatusResponse
            {
                Services = raw.ToDictionary(
                    kv => kv.Key,
                    kv => new ServiceHealthDto
                    {
                        Ok = kv.Value.Ok,
                        Detail = kv.Value.Detail
                    }),
                ChatModel = options.ChatModel,
                EmbeddingModel = options.EmbeddingModel,
                ScoreThresholdExact = options.ScoreThresholdExact,
                ScoreThresholdPartial = options.ScoreThresholdPartial,
                ScoreTolerance = options.ScoreTolerance
            });
        }
        catch (Exception e)
        {
            log.LogError(e, "GET /v1/status: failed");
            return TypedResults.Problem(detail: e.Message, statusCode: 502);
        }
    }

    private static async Task<Results<Ok<ChatResponse>, ProblemHttpResult>> PostChat(
        [FromBody] ChatRequest? body,
        [FromServices] VendorLookupAgent agent,
        [FromServices] AppOptions appOptions,
        [FromServices] ILogger<Program> log,
        [FromServices] IWebHostEnvironment env,
        CancellationToken cancellationToken)
    {
        if (body is null || string.IsNullOrWhiteSpace(body.Message))
        {
            return TypedResults.Problem(
                title: "Bad request",
                detail: "A non-empty JSON object with a \"message\" string is required.",
                statusCode: 400);
        }
        try
        {
            var t = body.Message.Trim();
            var (display, trace) = await agent.RunChatTurnAsync(t, cancellationToken);
            return TypedResults.Ok(new ChatResponse { DisplayMarkdown = display, TraceText = trace });
        }
        catch (Exception e)
        {
            log.LogError(e, "POST /v1/chat: turn failed");
            var showDetail = appOptions.ExposeErrorDetails || env.IsDevelopment();
            var detail = showDetail
                ? e.ToString()
                : "The chat service failed to process the request. Set VENDOR_LOOKUP_EXPOSE_ERROR_DETAILS=true or use Development to see the exception, or read API container logs.";
            return TypedResults.Problem(detail: detail, statusCode: 502);
        }
    }
}
