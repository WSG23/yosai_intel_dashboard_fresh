package config

import (
    "encoding/json"
    "io/ioutil"
    "os"

    pb "github.com/yosai-intel/dashboard/go/config/generated"
    "gopkg.in/yaml.v3"
)

// Load reads a configuration file in JSON or YAML format and returns a YosaiConfig struct.
func Load(path string) (*pb.YosaiConfig, error) {
    var data []byte
    var err error

    if path != "" {
        data, err = ioutil.ReadFile(path)
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
    return cfg, nil
}
