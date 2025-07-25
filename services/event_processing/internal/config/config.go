package config

import (
	"os"
	"strconv"

	"gopkg.in/yaml.v3"
)

// Config describes runtime configuration for the event processor.
type Config struct {
	Brokers string                 `yaml:"brokers"`
	GroupID string                 `yaml:"group_id"`
	Topic   string                 `yaml:"topic"`
	Breaker CircuitBreakerSettings `yaml:"breaker"`

}

// Load reads configuration from path. Environment variables override YAML.
func Load(path string) (*Config, error) {
	if path == "" {
		path = "config/event_processing.yaml"
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var cfg Config
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, err
	}

	if bc, err := LoadBreaker(""); err == nil {
		cfg.Breaker = bc.Repository
	}
	if v := os.Getenv("BROKERS"); v != "" {
		cfg.Brokers = v
	}
	if v := os.Getenv("GROUP_ID"); v != "" {
		cfg.GroupID = v
	}
	if v := os.Getenv("TOPIC"); v != "" {
		cfg.Topic = v
	}
	if v := os.Getenv("BREAKER_FAILURE_THRESHOLD"); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			cfg.Breaker.FailureThreshold = n
		}
	}
	if v := os.Getenv("BREAKER_RECOVERY_TIMEOUT"); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			cfg.Breaker.RecoveryTimeout = n

		}
	}
	if cfg.GroupID == "" {
		cfg.GroupID = "event-processing"
	}
	if cfg.Topic == "" {
		cfg.Topic = "events"
	}
	if cfg.Breaker.FailureThreshold == 0 {
		cfg.Breaker.FailureThreshold = 5
	}
	if cfg.Breaker.RecoveryTimeout == 0 {
		cfg.Breaker.RecoveryTimeout = 30

	}
	return &cfg, nil
}
