package events

import (
	"context"
	"encoding/json"
	"errors"
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

	if err := event.Validate(); err != nil {
		return err
	}

	event.ProcessedAt = time.Now()
	data, _ := json.Marshal(event)
	return ep.producer.Produce(&kafka.Message{
		TopicPartition: kafka.TopicPartition{Topic: &accessEventsTopic, Partition: kafka.PartitionAny},
		Value:          data,
	}, nil)
}
