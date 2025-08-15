package config

import (
	"encoding/json"
	"os"
	"strconv"
	"strings"
	"time"

	_ "embed"
	"github.com/xeipuuv/gojsonschema"
	"gopkg.in/yaml.v3"

	xerrors "github.com/WSG23/errors"
)

// CircuitBreakerSettings defines parameters for a gobreaker breaker.
type CircuitBreakerSettings struct {
	FailureThreshold int `yaml:"failure_threshold"`
	RecoveryTimeout  int `yaml:"recovery_timeout"`
}

// Config holds circuit breaker settings for services.
type Config struct {
	Database       CircuitBreakerSettings `yaml:"database"`
	ExternalAPI    CircuitBreakerSettings `yaml:"external_api"`
	EventProcessor CircuitBreakerSettings `yaml:"event_processor"`
}

//go:embed circuitbreakers_schema.json
var cbSchema []byte

// LoadCircuitBreakers reads YAML configuration from path. If path is empty, the default
// "config/circuit-breakers.yaml" is used.
func LoadCircuitBreakers(path string) (*Config, error) {
	if path == "" {
		path = "config/circuit-breakers.yaml"
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	var raw interface{}
	if err := yaml.Unmarshal(data, &raw); err != nil {
		return nil, err
	}
	jsonData, err := json.Marshal(raw)
	if err != nil {
		return nil, err
	}
	schemaLoader := gojsonschema.NewBytesLoader(cbSchema)
	docLoader := gojsonschema.NewBytesLoader(jsonData)
	result, err := gojsonschema.Validate(schemaLoader, docLoader)
	if err != nil {
		return nil, err
	}
	if !result.Valid() {
		msgs := make([]string, len(result.Errors()))
		for i, e := range result.Errors() {
			msgs[i] = e.String()
		}
		return nil, xerrors.Errorf("invalid configuration: %s", strings.Join(msgs, "; "))
	}

	var cfg Config
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, err
	}
	overrideEnv(&cfg)
	return &cfg, nil
}

func overrideEnv(cfg *Config) {
	if v := os.Getenv("CB_DATABASE_FAILURE_THRESHOLD"); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			cfg.Database.FailureThreshold = n
		}
	}
	if v := os.Getenv("CB_DATABASE_RECOVERY_TIMEOUT"); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			cfg.Database.RecoveryTimeout = n
		}
	}
	if v := os.Getenv("CB_EXTERNAL_API_FAILURE_THRESHOLD"); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			cfg.ExternalAPI.FailureThreshold = n
		}
	}
	if v := os.Getenv("CB_EXTERNAL_API_RECOVERY_TIMEOUT"); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			cfg.ExternalAPI.RecoveryTimeout = n
		}
	}
	if v := os.Getenv("CB_EVENT_PROCESSOR_FAILURE_THRESHOLD"); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			cfg.EventProcessor.FailureThreshold = n
		}
	}
	if v := os.Getenv("CB_EVENT_PROCESSOR_RECOVERY_TIMEOUT"); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			cfg.EventProcessor.RecoveryTimeout = n
		}
	}
}

// Timeout returns the timeout as time.Duration.
func (s CircuitBreakerSettings) Timeout() time.Duration {
	if s.RecoveryTimeout <= 0 {
		return 0
	}
	return time.Duration(s.RecoveryTimeout) * time.Second
}
