package config

import (
	"os"
	"testing"
)

func TestLoadValidConfig(t *testing.T) {
	cfg, err := LoadCircuitBreakers("../../../config/circuit-breakers.yaml")
	if err != nil {
		t.Fatalf("load valid: %v", err)
	}
	if cfg.Database.FailureThreshold == 0 {
		t.Fatalf("unexpected zero value")
	}
}

func TestLoadInvalidConfig(t *testing.T) {
	tmp, err := os.CreateTemp("", "bad*.yaml")
	if err != nil {
		t.Fatal(err)
	}
	defer os.Remove(tmp.Name())
	tmp.WriteString("database:\n  failure_threshold: 'x'\n")
	tmp.Close()

	if _, err := LoadCircuitBreakers(tmp.Name()); err == nil {
		t.Fatal("expected error")
	}
}
