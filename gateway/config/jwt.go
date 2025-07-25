package config

import (
	"os"
	"time"

	"gopkg.in/yaml.v3"
)

// JWTConfig describes how JWT validation should be performed.
type JWTConfig struct {
	Issuers []struct {
		Name       string `yaml:"name"`
		PublicKey  string `yaml:"public_key"`
		RefreshURL string `yaml:"refresh_url"`
	} `yaml:"issuers"`
	CacheTTL     time.Duration `yaml:"cache_ttl"`
	BlacklistTTL time.Duration `yaml:"blacklist_ttl"`
}

// LoadJWT reads configuration from path. If path is empty, "config/jwt.yaml" is used.
func LoadJWT(path string) (*JWTConfig, error) {
	if path == "" {
		path = "config/jwt.yaml"
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var cfg JWTConfig
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, err
	}
	return &cfg, nil
}
