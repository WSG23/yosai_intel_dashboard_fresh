package config

import (
	"os"

	"gopkg.in/yaml.v3"
)

type RateLimitSettings struct {
	PerIP   int `yaml:"per_ip"`
	PerUser int `yaml:"per_user"`
	PerKey  int `yaml:"per_key"`
	Global  int `yaml:"global"`
	Burst   int `yaml:"burst"`
}

func LoadRateLimit(path string) (*RateLimitSettings, error) {
	if path == "" {
		path = "config/ratelimit.yaml"
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var cfg RateLimitSettings
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, err
	}
	return &cfg, nil
}
