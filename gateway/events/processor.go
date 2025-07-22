package events

import (
	"context"
	"encoding/json"
	"time"

	"github.com/confluentinc/confluent-kafka-go/kafka"

	"github.com/WSG23/yosai-gateway/internal/cache"
)

var accessEventsTopic = "access-events"

type EventProcessor struct {
	producer *kafka.Producer
	consumer *kafka.Consumer
	cache    cache.CacheService
}

func NewEventProcessor(brokers string, c cache.CacheService) (*EventProcessor, error) {
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
	return &EventProcessor{producer: producer, consumer: consumer, cache: c}, nil
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
	// attempt to get cached decision first
	if ep.cache != nil {
		if d, err := ep.cache.GetDecision(context.Background(), event.PersonID, event.DoorID); err == nil && d != nil {
			event.AccessResult = d.Decision
			event.ProcessedAt = time.Now()
			data, _ := json.Marshal(event)
			return ep.producer.Produce(&kafka.Message{
				TopicPartition: kafka.TopicPartition{Topic: &accessEventsTopic, Partition: kafka.PartitionAny},
				Value:          data,
			}, nil)
		}
	}

	if err := event.Validate(); err != nil {
		return err
	}

	// compute decision according to access rules - not implemented here

	// store decision in cache if available
	if ep.cache != nil {
		_ = ep.cache.SetDecision(context.Background(), cache.Decision{
			PersonID: event.PersonID,
			DoorID:   event.DoorID,
			Decision: event.AccessResult,
		})
	}

	event.ProcessedAt = time.Now()
	data, _ := json.Marshal(event)
	return ep.producer.Produce(&kafka.Message{
		TopicPartition: kafka.TopicPartition{Topic: &accessEventsTopic, Partition: kafka.PartitionAny},
		Value:          data,
	}, nil)
}
