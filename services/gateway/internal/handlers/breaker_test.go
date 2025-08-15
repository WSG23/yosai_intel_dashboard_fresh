package handlers

import (
        "encoding/json"
        "errors"
        "net/http"
        "net/http/httptest"
        "testing"

        "github.com/prometheus/client_golang/prometheus"
        dto "github.com/prometheus/client_model/go"
)

type errorGatherer struct{}

func (errorGatherer) Gather() ([]*dto.MetricFamily, error) {
        return nil, errors.New("boom")
}

func TestBreakerMetricsSuccess(t *testing.T) {
        reg := prometheus.NewRegistry()
        ctr := prometheus.NewCounterVec(prometheus.CounterOpts{
                Name: "circuit_breaker_state_transitions_total",
                Help: "test",
        }, []string{"name", "state"})
        reg.MustRegister(ctr)
        ctr.WithLabelValues("svc", "open").Inc()

        old := prometheus.DefaultGatherer
        prometheus.DefaultGatherer = reg
        defer func() { prometheus.DefaultGatherer = old }()

        req := httptest.NewRequest(http.MethodGet, "/breaker", nil)
        resp := httptest.NewRecorder()
        BreakerMetrics(resp, req)

        if resp.Code != http.StatusOK {
                t.Fatalf("expected 200, got %d", resp.Code)
        }
        var out map[string]map[string]float64
        if err := json.Unmarshal(resp.Body.Bytes(), &out); err != nil {
                t.Fatalf("invalid json: %v", err)
        }
        if out["svc"]["open"] != 1 {
                t.Fatalf("expected metric, got %v", out)
        }
}

func TestBreakerMetricsError(t *testing.T) {
        old := prometheus.DefaultGatherer
        prometheus.DefaultGatherer = errorGatherer{}
        defer func() { prometheus.DefaultGatherer = old }()

        req := httptest.NewRequest(http.MethodGet, "/breaker", nil)
        resp := httptest.NewRecorder()
        BreakerMetrics(resp, req)

        if resp.Code != http.StatusInternalServerError {
                t.Fatalf("expected 500, got %d", resp.Code)
        }
}

