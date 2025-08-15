package monitoring

import "github.com/prometheus/client_golang/prometheus"

// Metrics for monitoring the synchronization between the outbox and
// access_events table.
var (
	// OutboxPending reports the number of events waiting to be processed.
	OutboxPending = prometheus.NewGauge(prometheus.GaugeOpts{
		Name: "timescale_outbox_pending",
		Help: "Number of events pending in the TimescaleDB outbox.",
	})

	// OutboxDivergences counts events that are missing from the primary table.
	OutboxDivergences = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "timescale_outbox_divergence_total",
		Help: "Total outbox events without a matching access event.",
	})
)

func init() {
	prometheus.MustRegister(OutboxPending, OutboxDivergences)
}
