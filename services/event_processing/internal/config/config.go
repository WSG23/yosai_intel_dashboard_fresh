package config

import (
	"os"
	"strconv"

	"gopkg.in/yaml.v3"
)

// Config describes runtime configuration for the event processor.
type Config struct {
	Brokers          string `yaml:"brokers"`
	GroupID          string `yaml:"group_id"`
	Topic            string `yaml:"topic"`
	FailureThreshold int    `yaml:"failure_threshold"`
	RecoveryTimeout  int    `yaml:"recovery_timeout"`
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
	if v := os.Getenv("BROKERS"); v != "" {
		cfg.Brokers = v
	}
	if v := os.Getenv("GROUP_ID"); v != "" {
		cfg.GroupID = v
	}
	if v := os.Getenv("TOPIC"); v != "" {
		cfg.Topic = v
	}
	if v := os.Getenv("CB_FAILURE_THRESHOLD"); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			cfg.FailureThreshold = n
		}
	}
	if v := os.Getenv("CB_RECOVERY_TIMEOUT"); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			cfg.RecoveryTimeout = n
		}
	}
	if cfg.GroupID == "" {
		cfg.GroupID = "event-processing"
	}
	if cfg.Topic == "" {
		cfg.Topic = "events"
	}
	if cfg.FailureThreshold == 0 {
		cfg.FailureThreshold = 5
	}
	if cfg.RecoveryTimeout == 0 {
		cfg.RecoveryTimeout = 30
	}
	return &cfg, nil
}
