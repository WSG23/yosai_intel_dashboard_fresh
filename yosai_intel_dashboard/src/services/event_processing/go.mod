module github.com/WSG23/yosai-event-processing

go 1.23.8


require (
        github.com/WSG23/resilience v0.0.0
        github.com/WSG23/yosai-framework v0.0.0
        github.com/WSG23/errors v0.0.0
        github.com/confluentinc/confluent-kafka-go v1.9.3-RC3
        github.com/prometheus/client_golang v1.22.0
        github.com/sony/gobreaker v1.0.0
	github.com/xeipuuv/gojsonschema v1.2.0

	gopkg.in/yaml.v3 v3.0.1
)

require (
	github.com/WSG23/yosai_intel_dashboard_fresh/shared/errors v0.0.0 // indirect
	github.com/beorn7/perks v1.0.1 // indirect
	github.com/cespare/xxhash/v2 v2.3.0 // indirect
	github.com/go-logr/logr v1.4.3 // indirect
	github.com/go-logr/stdr v1.2.2 // indirect
	github.com/google/uuid v1.6.0 // indirect
	github.com/munnerz/goautoneg v0.0.0-20191010083416-a7dc8b61c822 // indirect
	github.com/prometheus/client_model v0.6.2 // indirect
	github.com/prometheus/common v0.65.0 // indirect
	github.com/prometheus/procfs v0.17.0 // indirect
	github.com/xeipuuv/gojsonpointer v0.0.0-20180127040702-4e3ac2762d5f // indirect
	github.com/xeipuuv/gojsonreference v0.0.0-20180127040603-bd5ef7bd5415 // indirect
	go.opentelemetry.io/auto/sdk v1.1.0 // indirect
	go.opentelemetry.io/otel v1.37.0 // indirect
	go.opentelemetry.io/otel/exporters/jaeger v1.17.0 // indirect
	go.opentelemetry.io/otel/metric v1.37.0 // indirect
	go.opentelemetry.io/otel/sdk v1.37.0 // indirect
	go.opentelemetry.io/otel/trace v1.37.0 // indirect
	go.uber.org/multierr v1.10.0 // indirect
	go.uber.org/zap v1.26.0 // indirect
	golang.org/x/sys v0.34.0 // indirect
	google.golang.org/protobuf v1.36.6 // indirect

)

replace github.com/WSG23/yosai-framework => ../../go/framework

replace github.com/WSG23/resilience => ../../resilience


replace github.com/WSG23/yosai-gateway => ../../gateway

replace github.com/WSG23/yosai_intel_dashboard_fresh/shared/errors => ../../shared/errors

replace github.com/WSG23/errors => ../../../../pkg/errors
