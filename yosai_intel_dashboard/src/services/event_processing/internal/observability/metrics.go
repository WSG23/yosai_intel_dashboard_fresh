package observability

import (
    "net/http"

    "github.com/prometheus/client_golang/prometheus/promhttp"
)

// RegisterMetrics mounts the Prometheus handler on the given mux.
func RegisterMetrics(mux *http.ServeMux) {
    mux.Handle("/metrics", promhttp.Handler())
}

