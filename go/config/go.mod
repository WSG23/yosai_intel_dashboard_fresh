module github.com/yosai-intel/dashboard/go/config

go 1.23.0

toolchain go1.23.8

require (
    gopkg.in/yaml.v3 v3.0.1
    github.com/yosai-intel/dashboard/go/config/generated v0.0.0
)

replace github.com/yosai-intel/dashboard/go/config/generated => ./generated
