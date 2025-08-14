package events

import "testing"

func TestProducerConfig(t *testing.T) {
        cfg := producerConfig("b:1", "txid")
        if v, _ := cfg["enable.idempotence"].(bool); !v {
                t.Fatalf("idempotence not enabled")
        }
        if v, _ := cfg["acks"].(string); v != "all" {
                t.Fatalf("acks not all")
        }
        if v, _ := cfg["transactional.id"].(string); v != "txid" {
                t.Fatalf("transactional id mismatch")
        }
}

