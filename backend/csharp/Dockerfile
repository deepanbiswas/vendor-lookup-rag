# C# vendor lookup API (default listen port 8001 in-app; map host port in compose).
# Build context: repository root. Example: docker build -f backend/csharp/Dockerfile -t vendor-lookup-csharp:local .
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
WORKDIR /src
COPY backend/csharp/ ./backend/csharp/
RUN dotnet publish backend/csharp/src/VendorLookupRag/VendorLookupRag.csproj -c Release -o /out

FROM mcr.microsoft.com/dotnet/aspnet:9.0
# Only extra OS package: curl (not present in the base image) for the HTTP health check in docker-compose.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=build /out ./
EXPOSE 8001
ENV ASPNETCORE_URLS=
ENV VENDOR_LOOKUP_CSHARP_PORT=8001
ENTRYPOINT ["./VendorLookupRag"]
