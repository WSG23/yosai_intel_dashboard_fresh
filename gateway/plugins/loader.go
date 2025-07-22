package plugins

import (
	"gopkg.in/yaml.v3"
	"os"

	"github.com/WSG23/yosai-gateway/plugins/cache"
	"github.com/WSG23/yosai-gateway/plugins/ratelimit"
)

// yamlPluginConfig represents a plugin entry in gateway.yaml.
type yamlPluginConfig struct {
	Name    string                 `yaml:"name"`
	Enabled bool                   `yaml:"enabled"`
	Config  map[string]interface{} `yaml:"config"`
}

type yamlGatewayConfig struct {
	Gateway struct {
		Plugins []yamlPluginConfig `yaml:"plugins"`
	} `yaml:"gateway"`
}

// LoadPlugins parses gateway.yaml and returns instantiated plugins.
// If path is empty, "config/gateway.yaml" is used.
func LoadPlugins(path string) ([]Plugin, error) {
	if path == "" {
		path = "config/gateway.yaml"
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	var cfg yamlGatewayConfig
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, err
	}

	var pluginsList []Plugin
	for _, pc := range cfg.Gateway.Plugins {
		if !pc.Enabled {
			continue
		}
		switch pc.Name {
		case "rate-limit":
			rp := &ratelimit.RateLimitPlugin{}
			rp.Init(pc.Config)
			pluginsList = append(pluginsList, rp)
		case "cache":
			cp := &cache.CachePlugin{}
			cp.Init(pc.Config)
			pluginsList = append(pluginsList, cp)
		}
	}
	return pluginsList, nil
}
