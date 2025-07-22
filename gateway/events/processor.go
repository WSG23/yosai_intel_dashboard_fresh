package events

import (
	"context"
	"encoding/json"
	"log"
	"time"

	"github.com/confluentinc/confluent-kafka-go/kafka"

	"github.com/WSG23/yosai-gateway/internal/cache"
	"github.com/WSG23/yosai-gateway/internal/engine"
)

var accessEventsTopic = "access-events"

type EventProcessor struct {
	producer *kafka.Producer
	consumer *kafka.Consumer
	cache    cache.CacheService
	engine   *engine.CachedRuleEngine
}

func NewEventProcessor(brokers string, c cache.CacheService, e *engine.CachedRuleEngine) (*EventProcessor, error) {
	producer, err := kafka.NewProducer(&kafka.ConfigMap{"bootstrap.servers": brokers})
	if err != nil {
		return nil, err
	}
	consumer, err := kafka.NewConsumer(&kafka.ConfigMap{
		"bootstrap.servers": brokers,
		"group.id":          "gateway",
		"auto.offset.reset": "latest",
	})
	if err != nil {
		producer.Close()
		return nil, err
	}
	return &EventProcessor{producer: producer, consumer: consumer, cache: c, engine: e}, nil
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

func (ep *EventProcessor) ProcessAccessEvent(event AccessEvent) error {
	if ep.engine == nil {
		return errors.New("rule engine not configured")
	}

	dec, err := ep.engine.EvaluateAccess(context.Background(), event.PersonID, event.DoorID)
	if err != nil {
		return err
	}
	event.AccessResult = dec.Decision

	// compute decision according to access rules - not implemented here

	// store decision in cache if available
	if ep.cache != nil {
		if err := ep.cache.SetDecision(context.Background(), cache.Decision{
			PersonID: event.PersonID,
			DoorID:   event.DoorID,
			Decision: event.AccessResult,
		}); err != nil {
			// log failure but continue so access events are not lost
			log.Printf("failed to cache decision: %v", err)
		}

	}

	event.ProcessedAt = time.Now()
	data, _ := json.Marshal(event)
	return ep.producer.Produce(&kafka.Message{
		TopicPartition: kafka.TopicPartition{Topic: &accessEventsTopic, Partition: kafka.PartitionAny},
		Value:          data,
	}, nil)
}

// Run consumes AccessEvent messages from Kafka until ctx is cancelled. Messages
// are processed in batches and evaluated using a CachedRuleEngine.
func (ep *EventProcessor) Run(ctx context.Context) error {
	if err := ep.consumer.SubscribeTopics([]string{accessEventsTopic}, nil); err != nil {
		return err
	}

	engine := NewCachedRuleEngine(ep.cache)
	const batchSize = 50
	batch := make([]*kafka.Message, 0, batchSize)

	for {
		if ctx.Err() != nil {
			return nil
		}

		msg, err := ep.consumer.ReadMessage(500 * time.Millisecond)
		if err != nil {
			if kerr, ok := err.(kafka.Error); ok {
				if kerr.IsFatal() {
					return err
				}
				if kerr.IsRetriable() || kerr.Code() == kafka.ErrTimedOut {
					time.Sleep(time.Second)
					continue
				}
			}
			log.Printf("consumer error: %v", err)
			continue
		}

		batch = append(batch, msg)
		if len(batch) < batchSize {
			continue
		}

		for _, m := range batch {
			var ev AccessEvent
			if err := json.Unmarshal(m.Value, &ev); err != nil {
				log.Printf("malformed access event: %v", err)
				continue
			}
			if err := engine.Evaluate(ctx, &ev); err != nil {
				log.Printf("rule evaluation error: %v", err)
				continue
			}
			_, _ = ep.consumer.CommitMessage(m)
		}
		batch = batch[:0]
	}
}
