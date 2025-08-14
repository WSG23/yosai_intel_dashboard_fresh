package kafka

import (
	"context"
	"sync"

	ckafka "github.com/confluentinc/confluent-kafka-go/kafka"
)

// Consumer wraps a Kafka consumer using consumer groups.
type Consumer struct {
	c         *ckafka.Consumer
	processed sync.Map
}

// NewConsumer creates a new Consumer connected to brokers with the given groupID.
func NewConsumer(brokers, groupID string) (*Consumer, error) {
	cfg := &ckafka.ConfigMap{
		"bootstrap.servers": brokers,
		"group.id":          groupID,
		"auto.offset.reset": "earliest",
	}
	c, err := ckafka.NewConsumer(cfg)
	if err != nil {
		return nil, err
	}
	return &Consumer{c: c}, nil
}

// Consume subscribes to topics and invokes handler for each message until ctx is cancelled.
func (c *Consumer) Consume(ctx context.Context, topics []string, handler func(context.Context, *ckafka.Message) error) error {
	if err := c.c.SubscribeTopics(topics, nil); err != nil {
		return err
	}
	for {
		if ctx.Err() != nil {
			return ctx.Err()
		}
		msg, err := c.c.ReadMessage(100)
		if err != nil {
			if e, ok := err.(ckafka.Error); ok && (e.IsRetriable() || e.Code() == ckafka.ErrTimedOut) {
				continue
			}
			continue
		}
		if _, ok := c.processed.LoadOrStore(string(msg.Key), struct{}{}); ok {
			continue
		}
		if err := handler(ctx, msg); err == nil {
			_, _ = c.c.CommitMessage(msg)
		}
	}
}

// Close shuts down the consumer.
func (c *Consumer) Close() {
	if c.c != nil {
		c.c.Close()
	}
}
