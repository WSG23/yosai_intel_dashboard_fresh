package config

import (
	"os"
	"testing"
)

func TestEnvOverrides(t *testing.T) {
	os.Setenv("YOSAI_CONFIG_JSON", `{"app":{"title":"t"},"database":{"name":"db"},"security":{"secret_key":"x"}}`)
	os.Setenv("YOSAI_APP_TITLE", "override")
	os.Setenv("YOSAI_DATABASE_HOST", "db.example")
	defer os.Clearenv()

	cfg, err := Load("")
	if err != nil {
		t.Fatalf("load: %v", err)
	}
	if cfg.GetApp().GetTitle() != "override" {
		t.Fatalf("expected override got %s", cfg.GetApp().GetTitle())
	}
	if cfg.GetDatabase().GetHost() != "db.example" {
		t.Fatalf("expected db.example got %s", cfg.GetDatabase().GetHost())
	}
}

func TestValidation(t *testing.T) {
	os.Setenv("YOSAI_CONFIG_JSON", `{}`)
	defer os.Clearenv()

	if _, err := Load(""); err == nil {
		t.Fatal("expected error")
	}
}
