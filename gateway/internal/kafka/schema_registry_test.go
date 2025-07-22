package kafka

import (
	"encoding/binary"
	"testing"

	"github.com/riferrei/srclient"
	"github.com/sony/gobreaker"
)

func TestNewSchemaRegistryDefaultURL(t *testing.T) {
	t.Setenv("SCHEMA_REGISTRY_URL", "")
	sr := NewSchemaRegistry("", gobreaker.Settings{})
	if sr.client.GetSchemaRegistryURL() != "http://localhost:8081" {
		t.Fatalf("unexpected default url %s", sr.client.GetSchemaRegistryURL())
	}
}

func TestNewSchemaRegistryFromEnv(t *testing.T) {
	t.Setenv("SCHEMA_REGISTRY_URL", "http://sr:1234")
	sr := NewSchemaRegistry("", gobreaker.Settings{})
	if sr.client.GetSchemaRegistryURL() != "http://sr:1234" {
		t.Fatalf("unexpected url %s", sr.client.GetSchemaRegistryURL())
	}
}

func TestSchemaRegistrySerialize(t *testing.T) {
	mock := srclient.CreateMockSchemaRegistryClient("mock")
	schemaStr := `{"type":"record","name":"t","fields":[{"name":"f","type":"string"}]}`
	schema, err := mock.CreateSchema("test", schemaStr, srclient.Avro)
	if err != nil {
		t.Fatalf("create schema: %v", err)
	}
	sr := &SchemaRegistry{client: mock, breaker: gobreaker.NewCircuitBreaker(gobreaker.Settings{})}

	payload, err := sr.Serialize("test", struct {
		F string `json:"f"`
	}{F: "x"})
	if err != nil {
		t.Fatalf("serialize: %v", err)
	}
	if payload[0] != 0 {
		t.Fatalf("missing magic byte")
	}
	id := binary.BigEndian.Uint32(payload[1:5])
	if int(id) != schema.ID() {
		t.Fatalf("schema id mismatch %d != %d", id, schema.ID())
	}
	if len(payload) <= 5 {
		t.Fatalf("no data encoded")
	}
}

func TestSchemaRegistrySerializeErr(t *testing.T) {
	mock := srclient.CreateMockSchemaRegistryClient("mock")
	sr := &SchemaRegistry{client: mock, breaker: gobreaker.NewCircuitBreaker(gobreaker.Settings{})}
	if _, err := sr.Serialize("missing", struct{}{}); err == nil {
		t.Fatal("expected error")
	}
}
