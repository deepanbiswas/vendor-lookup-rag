using System.Text.Json;
using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Http.Json;
using VendorLookupRag;
using VendorLookupRag.Composition;
using VendorLookupRag.Configuration;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddProblemDetails();
builder.Services.ConfigureHttpJsonOptions(o =>
{
    o.SerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower;
    o.SerializerOptions.DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull;
});
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c => c.SwaggerDoc("v1", new() { Title = "Vendor Lookup API (C#)", Version = "0.1" }));

var options = AppOptionsFactory.FromEnvironment();
builder.Services.AddVendorLookupRagCore(options);

var app = builder.Build();
if (options.ApiPort > 0)
{
    app.Urls.Clear();
    app.Urls.Add($"http://0.0.0.0:{options.ApiPort}");
}
// Unhandled errors must return application/problem+json so HTTP clients (e.g. Streamlit) can read "detail".
// Do not use the HTML developer exception page here — it breaks non-browser API consumers.
app.UseExceptionHandler(handler => handler.Run(async context =>
{
    var f = context.Features.Get<IExceptionHandlerPathFeature>();
    if (f?.Error is not { } ex) return;
    var o = context.RequestServices.GetRequiredService<AppOptions>();
    var env = context.RequestServices.GetRequiredService<Microsoft.AspNetCore.Hosting.IWebHostEnvironment>();
    var show = o.ExposeErrorDetails || env.IsDevelopment();
    var detail = show
        ? ex.ToString()
        : "Unhandled error. Set VENDOR_LOOKUP_EXPOSE_ERROR_DETAILS=true or use Development, or read API container logs.";
    context.Response.StatusCode = StatusCodes.Status500InternalServerError;
    context.Response.ContentType = "application/problem+json";
    await context.Response.WriteAsJsonAsync(
        new
        {
            type = "https://tools.ietf.org/html/rfc9110#section-15.6.1",
            title = "Internal server error",
            status = 500,
            detail
        },
        context.RequestAborted);
}));
app.UseSwagger();
app.UseSwaggerUI();
app.MapGet("/", () => Results.Redirect("/swagger"));
app.MapVendorApi();
app.Run();

public partial class Program;
