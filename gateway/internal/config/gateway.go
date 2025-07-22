package config

import (
	"os"
	"time"

	"gopkg.in/yaml.v3"
)

// GatewayConfig represents gateway.yaml structure.
type GatewayConfig struct {
	Gateway struct {
		Plugins []PluginConfig `yaml:"plugins"`
	} `yaml:"gateway"`
}

// PluginConfig defines a plugin entry.
type PluginConfig struct {
	Name    string       `yaml:"name"`
	Enabled bool         `yaml:"enabled"`
	Config  CacheOptions `yaml:"config"`
}

// CacheOptions holds configuration for the cache plugin.
type CacheOptions struct {
	Rules []CacheRuleConfig `yaml:"rules"`
}

type CacheRuleConfig struct {
	Path            string        `yaml:"path"`
	TTL             time.Duration `yaml:"ttl"`
	VaryHeaders     []string      `yaml:"vary_headers"`
	VaryParams      []string      `yaml:"vary_params"`
	InvalidatePaths []string      `yaml:"invalidate_paths"`
}

// LoadGateway loads gateway configuration from the given path.
// If path is empty, "config/gateway.yaml" is used.
func LoadGateway(path string) (*GatewayConfig, error) {
	if path == "" {
		path = "config/gateway.yaml"
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var cfg GatewayConfig
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, err
	}
	return &cfg, nil
}
