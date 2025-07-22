package events

import (
	"encoding/json"
	"time"

	"github.com/confluentinc/confluent-kafka-go/kafka"
)

var accessEventsTopic = "access-events"

type EventProcessor struct {
	producer *kafka.Producer
	consumer *kafka.Consumer
}

func NewEventProcessor(brokers string) (*EventProcessor, error) {
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
	return &EventProcessor{producer: producer, consumer: consumer}, nil
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
