package config

import (
	"encoding/json"
	"fmt"
	"os"
	"reflect"
	"strconv"
	"strings"

	pb "github.com/yosai-intel/dashboard/go/config/generated/github.com/yosai-intel/dashboard/go/config/generated"
	"gopkg.in/yaml.v3"
)

// Load reads a configuration file in JSON or YAML format and returns a YosaiConfig struct.
func Load(path string) (*pb.YosaiConfig, error) {
	var data []byte
	var err error

	if path != "" {
		data, err = os.ReadFile(path)
		if err != nil {
			return nil, err
		}
	} else if env := os.Getenv("YOSAI_CONFIG_JSON"); env != "" {
		data = []byte(env)
	}

	if len(data) == 0 {
		return &pb.YosaiConfig{}, nil
	}

	if data[0] != '{' && data[0] != '[' {
		var obj interface{}
		if err := yaml.Unmarshal(data, &obj); err != nil {
			return nil, err
		}
		data, err = json.Marshal(obj)
		if err != nil {
			return nil, err
		}
	}

	cfg := &pb.YosaiConfig{}
	if err := json.Unmarshal(data, cfg); err != nil {
		return nil, err
	}
	applyEnvOverrides(cfg)
	if err := validate(cfg); err != nil {
		return nil, err
	}
	return cfg, nil
}

// applyEnvOverrides updates cfg fields from YOSAI_* environment variables.
func applyEnvOverrides(cfg *pb.YosaiConfig) {
	prefix := "YOSAI_"
	for _, e := range os.Environ() {
		kv := strings.SplitN(e, "=", 2)
		if len(kv) != 2 {
			continue
		}
		name, val := kv[0], kv[1]
		if !strings.HasPrefix(name, prefix) {
			continue
		}
		key := strings.TrimPrefix(name, prefix)
		parts := strings.SplitN(strings.ToLower(key), "_", 2)
		if len(parts) != 2 {
			continue
		}
		section, field := parts[0], parts[1]
		var target interface{}
		switch section {
		case "app":
			if cfg.App == nil {
				cfg.App = &pb.AppConfig{}
			}
			target = cfg.App
		case "database":
			if cfg.Database == nil {
				cfg.Database = &pb.DatabaseConfig{}
			}
			target = cfg.Database
		case "security":
			if cfg.Security == nil {
				cfg.Security = &pb.SecurityConfig{}
			}
			target = cfg.Security
		default:
			continue
		}
		setField(target, field, val)
	}
}

func setField(obj interface{}, name, value string) {
	v := reflect.ValueOf(obj).Elem()
	t := v.Type()
	for i := 0; i < t.NumField(); i++ {
		f := t.Field(i)
		tag := strings.Split(f.Tag.Get("json"), ",")[0]
		if strings.EqualFold(tag, name) || strings.EqualFold(f.Name, name) {
			switch f.Type.Kind() {
			case reflect.Int32, reflect.Int, reflect.Int64:
				if iv, err := strconv.Atoi(value); err == nil {
					v.Field(i).SetInt(int64(iv))
				}
			case reflect.Bool:
				v.Field(i).SetBool(strings.ToLower(value) == "true" || value == "1" || strings.ToLower(value) == "yes")
			case reflect.String:
				v.Field(i).SetString(value)
			}
			return
		}
	}
}

func validate(cfg *pb.YosaiConfig) error {
	missing := []string{}
	if cfg.App == nil {
		missing = append(missing, "app")
	}
	if cfg.Database == nil {
		missing = append(missing, "database")
	}
	if cfg.Security == nil {
		missing = append(missing, "security")
	}
	if len(missing) > 0 {
		return fmt.Errorf("missing configuration sections: %s", strings.Join(missing, ", "))
	}
	if strings.ToLower(cfg.Environment) == "production" && cfg.Security != nil && cfg.Security.SecretKey == "" {
		return fmt.Errorf("SECRET_KEY must be set for production")
	}
	return nil
}
