package kafka

import (
	"encoding/binary"
	"encoding/json"
	"errors"
	"os"

	"github.com/riferrei/srclient"
)

// SchemaRegistry wraps srclient.ISchemaRegistryClient and provides helper
// methods for schema-based serialization.
type SchemaRegistry struct {
	client srclient.ISchemaRegistryClient
}

// NewSchemaRegistry creates a SchemaRegistry using the given URL. If url is
// empty the SCHEMA_REGISTRY_URL environment variable is used and falls back
// to http://localhost:8081 when unset.
func NewSchemaRegistry(url string) *SchemaRegistry {
	if url == "" {
		url = os.Getenv("SCHEMA_REGISTRY_URL")
		if url == "" {
			url = "http://localhost:8081"
		}
	}
	c := srclient.NewSchemaRegistryClient(url)
	c.CodecCreationEnabled(true)
	return &SchemaRegistry{client: c}
}

// LatestSchema retrieves the latest schema for the given subject.
func (sr *SchemaRegistry) LatestSchema(subject string) (*srclient.Schema, error) {
	return sr.client.GetLatestSchema(subject)
}

// Serialize marshals v using the latest schema for subject and returns the
// binary Avro payload with Confluent framing.
func (sr *SchemaRegistry) Serialize(subject string, v interface{}) ([]byte, error) {
	schema, err := sr.client.GetLatestSchema(subject)
	if err != nil {
		return nil, err
	}
	codec := schema.Codec()
	if codec == nil {
		return nil, errors.New("no codec for schema")
	}
	jsonBytes, err := json.Marshal(v)
	if err != nil {
		return nil, err
	}
	native, _, err := codec.NativeFromTextual(jsonBytes)
	if err != nil {
		return nil, err
	}
	avroData, err := codec.BinaryFromNative(nil, native)
	if err != nil {
		return nil, err
	}
	header := make([]byte, 5)
	header[0] = 0
	binary.BigEndian.PutUint32(header[1:], uint32(schema.ID()))
	return append(header, avroData...), nil
}
