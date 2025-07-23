package framework

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"strings"

	"github.com/xeipuuv/gojsonschema"
	"gopkg.in/yaml.v3"
)

type Config struct {
	ServiceName     string `yaml:"service_name"`
	LogLevel        string `yaml:"log_level"`
	MetricsAddr     string `yaml:"metrics_addr"`
	TracingEndpoint string `yaml:"tracing_endpoint"`
}

var schemaPath = "../config/service.schema.yaml"

func LoadConfig(path string) (Config, error) {
	var cfg Config
	data, err := ioutil.ReadFile(path)
	if err != nil {
		return cfg, err
	}
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return cfg, err
	}
	if err := validateConfig(data); err != nil {
		return cfg, err
	}
	applyEnv(&cfg)
	return cfg, nil
}

func applyEnv(cfg *Config) {
	for _, env := range os.Environ() {
		if strings.HasPrefix(env, "YOSAI_") {
			pair := strings.SplitN(env, "=", 2)
			key := strings.ToLower(strings.TrimPrefix(pair[0], "YOSAI_"))
			switch key {
			case "service_name":
				cfg.ServiceName = pair[1]
			case "log_level":
				cfg.LogLevel = pair[1]
			case "metrics_addr":
				cfg.MetricsAddr = pair[1]
			case "tracing_endpoint":
				cfg.TracingEndpoint = pair[1]
			}
		}
	}
}

func validateConfig(yamlData []byte) error {
	var obj interface{}
	if err := yaml.Unmarshal(yamlData, &obj); err != nil {
		return err
	}
	jsonBytes, err := json.Marshal(obj)
	if err != nil {
		return err
	}
	loader := gojsonschema.NewReferenceLoader("file://" + schemaPath)
	docLoader := gojsonschema.NewBytesLoader(jsonBytes)
	result, err := gojsonschema.Validate(loader, docLoader)
	if err != nil {
		return err
	}
	if !result.Valid() {
		return fmt.Errorf("config validation failed: %v", result.Errors())
	}
	return nil
}
