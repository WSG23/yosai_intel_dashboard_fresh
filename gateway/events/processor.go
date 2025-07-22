package events

import (
	"context"
	"encoding/json"
	"errors"
	"log"
	"time"

	ckafka "github.com/confluentinc/confluent-kafka-go/kafka"

	"github.com/WSG23/yosai-gateway/internal/cache"
	"github.com/WSG23/yosai-gateway/internal/engine"
	ikafka "github.com/WSG23/yosai-gateway/internal/kafka"
)

var accessEventsTopic = "access-events"

type EventProcessor struct {
	producer *ckafka.Producer
	consumer *ckafka.Consumer
	cache    cache.CacheService
	engine   *engine.CachedRuleEngine
	registry *ikafka.SchemaRegistry
}

func NewEventProcessor(brokers string, c cache.CacheService, e *engine.CachedRuleEngine) (*EventProcessor, error) {
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
	reg := ikafka.NewSchemaRegistry("")
	return &EventProcessor{producer: producer, consumer: consumer, cache: c, engine: e, registry: reg}, nil
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
	var data []byte
	if ep.registry != nil {
		record, err := ep.registry.Serialize("access-events-value", event)
		if err != nil {
			log.Printf("schema serialization failed: %v", err)
			data, _ = json.Marshal(event)
		} else {
			data = record
		}
	} else {
		data, _ = json.Marshal(event)
	}
	return ep.producer.Produce(&ckafka.Message{
		TopicPartition: ckafka.TopicPartition{Topic: &accessEventsTopic, Partition: ckafka.PartitionAny},
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
	batch := make([]*ckafka.Message, 0, batchSize)

	for {
		if ctx.Err() != nil {
			return nil
		}

		msg, err := ep.consumer.ReadMessage(500 * time.Millisecond)
		if err != nil {
			if kerr, ok := err.(ckafka.Error); ok {
				if kerr.IsFatal() {
					return err
				}
				if kerr.IsRetriable() || kerr.Code() == ckafka.ErrTimedOut {
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
