using Qdrant.Client.Grpc;
using VendorLookupRag.Adapters.Qdrant;

namespace VendorLookupRag.Tests.Adapters;

public class QdrantScoredPointMappingTests
{
    [Fact]
    public void ToVendorRecord_maps_core_string_payloads()
    {
        var p = new ScoredPoint
        {
            Score = 0.91f
        };
        p.Payload.Add("vendor_id", new Qdrant.Client.Grpc.Value { StringValue = "VID1" });
        p.Payload.Add("legal_name", new Qdrant.Client.Grpc.Value { StringValue = "Example AG" });
        p.Payload.Add("city", new Qdrant.Client.Grpc.Value { StringValue = "Berlin" });
        p.Payload.Add("vat_id", new Qdrant.Client.Grpc.Value { StringValue = "DE123" });
        p.Payload.Add("country", new Qdrant.Client.Grpc.Value { StringValue = "DE" });

        var r = QdrantScoredPointMapping.ToVendorRecord(p);
        Assert.NotNull(r);
        Assert.Equal("VID1", r!.VendorId);
        Assert.Equal("Example AG", r.LegalName);
        Assert.Equal("Berlin", r.City);
        Assert.Equal("DE123", r.VatId);
        Assert.Equal("DE", r.Country);
    }

    [Fact]
    public void ToVendorRecord_maps_extras_struct_string_fields()
    {
        var s = new Struct();
        s.Fields["custom_a"] = new Qdrant.Client.Grpc.Value { StringValue = "A" };
        s.Fields["custom_b"] = new Qdrant.Client.Grpc.Value { StringValue = "B" };

        var p = new ScoredPoint { Score = 0.5f };
        p.Payload.Add("vendor_id", new Qdrant.Client.Grpc.Value { StringValue = "x" });
        p.Payload.Add("legal_name", new Qdrant.Client.Grpc.Value { StringValue = "L" });
        p.Payload.Add("extras", new Qdrant.Client.Grpc.Value { StructValue = s });

        var r = QdrantScoredPointMapping.ToVendorRecord(p);
        Assert.NotNull(r);
        Assert.Equal(2, r!.Extras.Count);
        Assert.Equal("A", r.Extras["custom_a"]);
        Assert.Equal("B", r.Extras["custom_b"]);
    }
}
