package handlers

import (
	"encoding/json"
	"net/http"

	"github.com/prometheus/client_golang/prometheus"
)

// BreakerMetrics returns the circuit breaker state transition counters as JSON.
//
// @Summary      Circuit breaker metrics
// @Description  Returns Prometheus counters for circuit breaker state transitions
// @Tags         system
// @Produce      json
// @Success      200  {object}  map[string]map[string]float64
// @Failure      500  {string}  string  "internal server error"
// @Router       /breaker [get]
func BreakerMetrics(w http.ResponseWriter, r *http.Request) {
	metrics, err := prometheus.DefaultGatherer.Gather()
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		return
	}
	stats := make(map[string]map[string]float64)
	for _, mf := range metrics {
		if mf.GetName() != "circuit_breaker_state_transitions_total" {
			continue
		}
		for _, m := range mf.Metric {
			var name, state string
			for _, l := range m.Label {
				switch l.GetName() {
				case "name":
					name = l.GetValue()
				case "state":
					state = l.GetValue()
				}
			}
			if _, ok := stats[name]; !ok {
				stats[name] = map[string]float64{}
			}
			stats[name][state] = m.GetCounter().GetValue()
		}
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(stats)
}
