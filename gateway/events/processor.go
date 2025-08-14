package events

import (
	"context"
	"encoding/json"
	"errors"
	"time"

	"github.com/WSG23/resilience"
	"github.com/WSG23/yosai-gateway/internal/tracing"
	ckafka "github.com/confluentinc/confluent-kafka-go/kafka"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/sony/gobreaker"

	"go.opentelemetry.io/otel"

	"github.com/WSG23/yosai-gateway/internal/cache"
	"github.com/WSG23/yosai-gateway/internal/engine"
	ikafka "github.com/WSG23/yosai-gateway/internal/kafka"
)

var accessEventsTopic = "access-events"

var (
	eventsProcessed = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "event_processor_events_processed_total",
		Help: "Number of access events processed",
	})
)

func init() {
	prometheus.MustRegister(eventsProcessed)
}

type EventProcessor struct {
	producer *ckafka.Producer
	consumer *ckafka.Consumer
	cache    cache.CacheService
	engine   *engine.CachedRuleEngine
	registry *ikafka.SchemaRegistry
	breaker  *gobreaker.CircuitBreaker
}

func NewEventProcessor(brokers string, c cache.CacheService, e *engine.CachedRuleEngine, settings gobreaker.Settings) (*EventProcessor, error) {
	producer, err := ckafka.NewProducer(&ckafka.ConfigMap{"bootstrap.servers": brokers})
	if err != nil {
		return nil, err
	}
	consumer, err := ckafka.NewConsumer(&ckafka.ConfigMap{
		"bootstrap.servers": brokers,
		"group.id":          "gateway",
		"auto.offset.reset": "latest",
	})
	if err != nil {
		producer.Close()
		return nil, err
	}
	reg := ikafka.NewSchemaRegistry("", settings)
	cb := resilience.NewGoBreaker("event-processor", settings)
	return &EventProcessor{producer: producer, consumer: consumer, cache: c, engine: e, registry: reg, breaker: cb}, nil
}

func (ep *EventProcessor) Close() {
	if ep.consumer != nil {
		ep.consumer.Close()
	}
	if ep.producer != nil {
		ep.producer.Flush(5000)
		ep.producer.Close()
	}
}

func (ep *EventProcessor) ProcessAccessEvent(ctx context.Context, event AccessEvent) error {
	ctx, span := otel.Tracer("event-processor").Start(ctx, "ProcessAccessEvent")
	defer span.End()

	if ep.engine == nil {
		return errors.New("rule engine not configured")
	}

	dec, err := ep.engine.EvaluateAccess(ctx, event.PersonID, event.DoorID)
	if err != nil {
		return err
	}
	event.AccessResult = dec.Decision

	// compute decision according to access rules - not implemented here

	// store decision in cache if available
	if ep.cache != nil {
		if err := ep.cache.SetDecision(ctx, cache.Decision{
			PersonID: event.PersonID,
			DoorID:   event.DoorID,
			Decision: event.AccessResult,
		}); err != nil {
			// log failure but continue so access events are not lost
			tracing.Logger.WithError(err).Warn("failed to cache decision")
		}

	}

	event.ProcessedAt = time.Now()
	var data []byte
	if ep.registry != nil {
		record, err := ep.registry.Serialize("access-events-value", event)
		if err != nil {
			tracing.Logger.WithError(err).Warn("schema serialization failed")
			data, _ = json.Marshal(event)
		} else {
			data = record
		}
	} else {
		data, _ = json.Marshal(event)
	}
	eventsProcessed.Inc()
	_, err = ep.breaker.Execute(func() (interface{}, error) {
		_, pSpan := otel.Tracer("event-processor").Start(ctx, "kafka.produce")
		defer pSpan.End()
		err := ep.producer.Produce(&ckafka.Message{
			TopicPartition: ckafka.TopicPartition{Topic: &accessEventsTopic, Partition: ckafka.PartitionAny},
			Value:          data,
		}, nil)
		if err != nil {
			pSpan.RecordError(err)
		}
		return nil, err
	})
	return err

}

// Run consumes AccessEvent messages from Kafka until ctx is cancelled. Messages
// are processed in batches and evaluated using a CachedRuleEngine.
func (ep *EventProcessor) Run(ctx context.Context) error {
	ctx, span := otel.Tracer("event-processor").Start(ctx, "Run")
	defer span.End()
	if err := ep.consumer.SubscribeTopics([]string{accessEventsTopic}, nil); err != nil {
		return err
	}

	engine := NewCachedRuleEngine(ep.cache)
	const batchSize = 50
	batch := make([]*ckafka.Message, 0, batchSize)

	for {
		if ctx.Err() != nil {
			return nil
		}

		_, rSpan := otel.Tracer("event-processor").Start(ctx, "kafka.read")
		msg, err := ep.consumer.ReadMessage(500 * time.Millisecond)
		if err != nil {
			rSpan.RecordError(err)
			rSpan.End()
			if kerr, ok := err.(ckafka.Error); ok {
				if kerr.IsFatal() {
					return err
				}
				if kerr.IsRetriable() || kerr.Code() == ckafka.ErrTimedOut {
					time.Sleep(time.Second)
					continue
				}
			}
			tracing.Logger.WithError(err).Error("consumer error")
			continue
		}
		rSpan.End()

		batch = append(batch, msg)
		if len(batch) < batchSize {
			continue
		}

		for _, m := range batch {
			spanCtx, span := otel.Tracer("event-processor").Start(ctx, "process_event")
			var ev AccessEvent
			if err := json.Unmarshal(m.Value, &ev); err != nil {
				tracing.Logger.WithContext(spanCtx).WithError(err).Warn("malformed access event")
				span.End()
				continue
			}
			if err := engine.Evaluate(spanCtx, &ev); err != nil {
				tracing.Logger.WithContext(spanCtx).WithError(err).Warn("rule evaluation error")
				span.End()
				continue
			}
			eventsProcessed.Inc()
			_, _ = ep.consumer.CommitMessage(m)
			span.End()
		}

		batch = batch[:0]
	}
}
