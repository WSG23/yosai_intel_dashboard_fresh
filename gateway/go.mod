module github.com/WSG23/yosai-gateway

go 1.23.8

require github.com/gorilla/mux v1.8.1

require (
	github.com/DATA-DOG/go-sqlmock v1.5.2
	github.com/WSG23/auth v0.0.0
	github.com/WSG23/errors v0.0.0
        github.com/WSG23/resilience v0.0.0
        github.com/WSG23/yosai-framework v0.0.0
        github.com/WSG23/yosai_intel_dashboard_fresh/shared/errors v0.0.0
       github.com/WSG23/httpx v0.0.0
        github.com/alicebob/miniredis/v2 v2.35.0
	github.com/bits-and-blooms/bloom/v3 v3.7.0
	github.com/confluentinc/confluent-kafka-go v1.9.3-RC3
	github.com/golang-jwt/jwt/v5 v5.2.3
	github.com/gorilla/websocket v1.5.0
	github.com/hashicorp/consul/api v1.32.1
	github.com/hashicorp/golang-lru v1.0.2
	github.com/hashicorp/vault/api v1.20.0
	github.com/lib/pq v1.10.9
	github.com/prometheus/client_golang v1.22.0
	github.com/rabbitmq/amqp091-go v1.8.1
	github.com/redis/go-redis/v9 v9.11.0
	github.com/riferrei/srclient v0.7.3
	github.com/sirupsen/logrus v1.9.3
	github.com/sony/gobreaker v1.0.0
	github.com/xeipuuv/gojsonschema v1.2.0
	go.opentelemetry.io/otel v1.37.0
	go.opentelemetry.io/otel/exporters/jaeger v1.17.0
	go.opentelemetry.io/otel/exporters/zipkin v1.17.0
	go.opentelemetry.io/otel/sdk v1.37.0
	go.opentelemetry.io/otel/trace v1.37.0
	golang.org/x/time v0.8.0
	gopkg.in/yaml.v3 v3.0.1

)

require (
	github.com/armon/go-metrics v0.4.1 // indirect
	github.com/beorn7/perks v1.0.1 // indirect
	github.com/bits-and-blooms/bitset v1.10.0 // indirect
	github.com/cenkalti/backoff/v4 v4.3.0 // indirect
	github.com/cespare/xxhash/v2 v2.3.0 // indirect
	github.com/dgryski/go-rendezvous v0.0.0-20200823014737-9f7001d12a5f // indirect
	github.com/fatih/color v1.18.0 // indirect
	github.com/go-jose/go-jose/v4 v4.0.5 // indirect
	github.com/go-logr/logr v1.4.3 // indirect
	github.com/go-logr/stdr v1.2.2 // indirect
	github.com/golang/snappy v1.0.0 // indirect
	github.com/google/uuid v1.6.0 // indirect
	github.com/hashicorp/errwrap v1.1.0 // indirect
	github.com/hashicorp/go-cleanhttp v0.5.2 // indirect
	github.com/hashicorp/go-hclog v1.6.3 // indirect
	github.com/hashicorp/go-immutable-radix v1.3.1 // indirect
	github.com/hashicorp/go-metrics v0.5.4 // indirect
	github.com/hashicorp/go-multierror v1.1.1 // indirect
	github.com/hashicorp/go-retryablehttp v0.7.7 // indirect
	github.com/hashicorp/go-rootcerts v1.0.2 // indirect
	github.com/hashicorp/go-secure-stdlib/parseutil v0.1.6 // indirect
	github.com/hashicorp/go-secure-stdlib/strutil v0.1.2 // indirect
	github.com/hashicorp/go-sockaddr v1.0.5 // indirect
	github.com/hashicorp/hcl v1.0.1-vault-7 // indirect
	github.com/hashicorp/serf v0.10.2 // indirect
	github.com/linkedin/goavro/v2 v2.14.0 // indirect
	github.com/mattn/go-colorable v0.1.14 // indirect
	github.com/mattn/go-isatty v0.0.20 // indirect
	github.com/mitchellh/go-homedir v1.1.0 // indirect
	github.com/mitchellh/mapstructure v1.5.0 // indirect
	github.com/munnerz/goautoneg v0.0.0-20191010083416-a7dc8b61c822 // indirect
	github.com/openzipkin/zipkin-go v0.4.2 // indirect
	github.com/prometheus/client_model v0.6.2 // indirect
	github.com/prometheus/common v0.65.0 // indirect
	github.com/prometheus/procfs v0.17.0 // indirect
	github.com/ryanuber/go-glob v1.0.0 // indirect
	github.com/santhosh-tekuri/jsonschema/v5 v5.3.1 // indirect
	github.com/xeipuuv/gojsonpointer v0.0.0-20180127040702-4e3ac2762d5f // indirect
	github.com/xeipuuv/gojsonreference v0.0.0-20180127040603-bd5ef7bd5415 // indirect
	github.com/yuin/gopher-lua v1.1.1 // indirect
	go.opentelemetry.io/auto/sdk v1.1.0 // indirect
	go.opentelemetry.io/otel/metric v1.37.0 // indirect
	go.uber.org/multierr v1.10.0 // indirect
	go.uber.org/zap v1.26.0 // indirect
	golang.org/x/crypto v0.39.0 // indirect
	golang.org/x/exp v0.0.0-20250718183923-645b1fa84792 // indirect
	golang.org/x/net v0.41.0 // indirect
	golang.org/x/sync v0.16.0 // indirect
	golang.org/x/sys v0.34.0 // indirect
	golang.org/x/text v0.26.0 // indirect
	google.golang.org/protobuf v1.36.6 // indirect
)

replace github.com/WSG23/yosai-framework => ../go/framework

replace github.com/WSG23/yosai_intel_dashboard_fresh/shared/errors => ../shared/errors

replace github.com/WSG23/errors => ../pkg/errors

replace github.com/WSG23/auth => ../pkg/auth

replace github.com/WSG23/resilience => ../resilience

replace github.com/WSG23/httpx => ../pkg/httpx
