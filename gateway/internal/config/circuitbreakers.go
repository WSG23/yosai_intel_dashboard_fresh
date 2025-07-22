package config

import (
	"os"
	"time"

	"gopkg.in/yaml.v3"
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

// Load reads YAML configuration from path. If path is empty, the default
// "config/circuit-breakers.yaml" is used.
func Load(path string) (*Config, error) {
	if path == "" {
		path = "config/circuit-breakers.yaml"
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var cfg Config
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
