package config

import (
	"os"

	"gopkg.in/yaml.v3"
)

// Config describes runtime configuration for the event processor.
type Config struct {
	Brokers string `yaml:"brokers"`
	GroupID string `yaml:"group_id"`
	Topic   string `yaml:"topic"`
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
	if cfg.GroupID == "" {
		cfg.GroupID = "event-processing"
	}
	if cfg.Topic == "" {
		cfg.Topic = "events"
	}
	return &cfg, nil
}
