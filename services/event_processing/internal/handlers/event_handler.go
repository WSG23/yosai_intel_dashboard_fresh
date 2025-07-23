package handlers

import (
	"context"
	"encoding/json"
	"time"

	ckafka "github.com/confluentinc/confluent-kafka-go/kafka"

	"github.com/WSG23/resilience"
	"github.com/WSG23/yosai-event-processing/internal/repository"
	"github.com/WSG23/yosai-event-processing/pkg/events"
	"github.com/WSG23/yosai-event-processing/pkg/metrics"
)

// EventHandler processes Kafka messages with idempotency and saga coordination.
type EventHandler struct {
	store   repository.TokenStore
	breaker *resilience.CircuitBreaker
}

func NewEventHandler(store repository.TokenStore) *EventHandler {
	b := resilience.New("repo", 5, 5*time.Second, 10, 0.7)
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
		return h.breaker.Execute(c, func(context.Context) error {
			return h.store.MarkProcessed(c, ev.ID)
		}, nil)
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
