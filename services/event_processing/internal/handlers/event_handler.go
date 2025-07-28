package handlers

import (
	"context"
	"encoding/json"

	ckafka "github.com/confluentinc/confluent-kafka-go/kafka"
	"github.com/sony/gobreaker"

	"github.com/WSG23/resilience"
	"github.com/WSG23/yosai-event-processing/internal/repository"
	"github.com/WSG23/yosai-event-processing/pkg/events"
	"github.com/WSG23/yosai-event-processing/pkg/metrics"
)

// EventHandler processes Kafka messages with idempotency and saga coordination.
type EventHandler struct {
	store   repository.TokenStore
	breaker *gobreaker.CircuitBreaker
}

// NewEventHandler creates an EventHandler using the provided settings.
func NewEventHandler(store repository.TokenStore, settings gobreaker.Settings) *EventHandler {
	if settings.Name == "" {
		settings.Name = "repo"
	}
	if settings.Timeout == 0 {
		settings.Timeout = 5 * time.Second
	}
	if settings.ReadyToTrip == nil {
		settings.ReadyToTrip = func(c gobreaker.Counts) bool { return c.ConsecutiveFailures > 5 }
	}
	b := resilience.NewGoBreaker(settings.Name, settings)

	return &EventHandler{store: store, breaker: b}
}

// HandleMessage decodes and processes an event.
func (h *EventHandler) HandleMessage(ctx context.Context, msg *ckafka.Message) error {
	var ev events.Event
	if err := json.Unmarshal(msg.Value, &ev); err != nil {
		metrics.EventsFailed.Inc()
		return err
	}
	processed, err := h.store.IsProcessed(ctx, ev.ID)
	if err != nil {
		metrics.EventsFailed.Inc()
		return err
	}
	if processed {
		return nil
	}
	saga := NewSaga()
	saga.AddStep(func(c context.Context) error {
		_, err := h.breaker.Execute(func() (interface{}, error) {
			return nil, h.store.MarkProcessed(c, ev.ID)
		})
		return err
	}, func(c context.Context) error {
		return h.store.Rollback(c, ev.ID)
	})

	if err := saga.Execute(ctx); err != nil {
		metrics.EventsFailed.Inc()
		return err
	}

	metrics.EventsProcessed.Inc()
	return nil
}
