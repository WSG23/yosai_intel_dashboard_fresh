package config

import (
	"encoding/json"
	"os"
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

// Config holds circuit breaker settings for this service.
type BreakerConfig struct {
	Repository CircuitBreakerSettings `yaml:"repository"`
}

//go:embed circuitbreakers_schema.json
var cbSchema []byte

// LoadBreaker reads YAML configuration from path or defaults to "config/circuit-breakers.yaml".
func LoadBreaker(path string) (*BreakerConfig, error) {
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

	var cfg BreakerConfig
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, err
	}
	return &cfg, nil
}

// Timeout returns the timeout as time.Duration.
func (s CircuitBreakerSettings) Timeout() time.Duration {
	if s.RecoveryTimeout <= 0 {
		return 0
	}
	return time.Duration(s.RecoveryTimeout) * time.Second
}
