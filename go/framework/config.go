package framework

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"strconv"
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

const defaultSchemaPath = "../../config/service.schema.yaml"

func schemaPath() string {
	if path := os.Getenv("YOSAI_SCHEMA_PATH"); path != "" {
		return path
	}
	return defaultSchemaPath
}

func LoadConfig(path string) (Config, error) {
	var cfg Config
	data, err := os.ReadFile(path)
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
	if errs := validateYosaiConfig(cfg); len(errs) > 0 {
		return cfg, errors.New(strings.Join(errs, "; "))
	}
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
	loader := gojsonschema.NewReferenceLoader("file://" + schemaPath())
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

func validateYosaiConfig(cfg Config) []string {
	var errs []string
	if cfg.ServiceName == "" {
		errs = append(errs, "service_name is required")
	}
	switch strings.ToUpper(cfg.LogLevel) {
	case "DEBUG", "INFO", "WARN", "ERROR":
	default:
		errs = append(errs, "log_level must be one of DEBUG, INFO, WARN, ERROR")
	}
	if cfg.MetricsAddr != "" {
		parts := strings.Split(cfg.MetricsAddr, ":")
		if len(parts) != 2 {
			errs = append(errs, "metrics_addr must be in host:port format")
		} else {
			port, err := strconv.Atoi(parts[1])
			if err != nil || port <= 0 || port > 65535 {
				errs = append(errs, "metrics_addr port must be 1-65535")
			}
		}
	} else if strings.ToUpper(cfg.LogLevel) == "DEBUG" {
		errs = append(errs, "metrics_addr required when log_level is DEBUG")
	}
	if cfg.TracingEndpoint != "" && !strings.HasPrefix(cfg.TracingEndpoint, "http://") && !strings.HasPrefix(cfg.TracingEndpoint, "https://") {
		errs = append(errs, "tracing_endpoint must start with http:// or https://")
	}
	if cfg.MetricsAddr != "" && cfg.MetricsAddr == cfg.TracingEndpoint {
		errs = append(errs, "metrics_addr and tracing_endpoint must differ")
	}
	return errs
}
