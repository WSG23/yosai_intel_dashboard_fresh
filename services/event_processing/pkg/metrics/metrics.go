package metrics

import "github.com/prometheus/client_golang/prometheus"

var (
	EventsProcessed = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "event_processing_events_processed_total",
		Help: "Total number of events processed successfully",
	})
	EventsFailed = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "event_processing_events_failed_total",
		Help: "Total number of events that failed processing",
	})
)

func init() {
	prometheus.MustRegister(EventsProcessed, EventsFailed)
}
