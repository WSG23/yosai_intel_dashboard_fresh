package queue

import (
	"context"
	"encoding/json"
	"sync"

	"github.com/prometheus/client_golang/prometheus"

	"github.com/WSG23/queue/rabbitmq"
)

// DLQMessages counts messages published to a dead-letter queue.
var DLQMessages = prometheus.NewCounterVec(
	prometheus.CounterOpts{
		Name: "queue_dlq_messages_total",
		Help: "Number of messages sent to the dead-letter queue",
	},
	[]string{"queue"},
)

// ProcessedMessages counts successfully handled tasks.
var ProcessedMessages = prometheus.NewCounterVec(
	prometheus.CounterOpts{
		Name: "queue_processed_messages_total",
		Help: "Number of messages processed successfully",
	},
	[]string{"queue"},
)

// ProcessingErrors counts task handler failures.
var ProcessingErrors = prometheus.NewCounterVec(
	prometheus.CounterOpts{
		Name: "queue_processing_errors_total",
		Help: "Number of errors while processing messages",
	},
	[]string{"queue"},
)

func init() {
	prometheus.MustRegister(DLQMessages, ProcessedMessages, ProcessingErrors)
}

// DLQProducer publishes tasks to a dead-letter queue.
type DLQProducer interface {
	Publish(ctx context.Context, queue string, task *rabbitmq.Task) error
}

// Consumer processes tasks from a queue with idempotency and DLQ support.
type Consumer struct {
	queue string
	dlq   string
	p     DLQProducer

	processed sync.Map
}

// NewConsumer creates a new Consumer for queue with the provided DLQ producer.
func NewConsumer(queue, dlq string, producer DLQProducer) *Consumer {
	return &Consumer{queue: queue, dlq: dlq, p: producer}
}

// Process handles a raw message, invoking handler and routing failures to the DLQ.
func (c *Consumer) Process(ctx context.Context, msg []byte, handler func(context.Context, *rabbitmq.Task) error) error {
	var t rabbitmq.Task
	if err := json.Unmarshal(msg, &t); err != nil {
		DLQMessages.WithLabelValues(c.queue).Inc()
		if c.p != nil {
			_ = c.p.Publish(ctx, c.dlq, &rabbitmq.Task{Payload: msg})
		}
		return err
	}
	if _, ok := c.processed.LoadOrStore(t.ID, struct{}{}); ok {
		return nil
	}
	if err := handler(ctx, &t); err != nil {
		t.RetryCount++
		ProcessingErrors.WithLabelValues(c.queue).Inc()
		if t.MaxRetries > 0 && t.RetryCount >= t.MaxRetries {
			DLQMessages.WithLabelValues(c.queue).Inc()
			if c.p != nil {
				_ = c.p.Publish(ctx, c.dlq, &t)
			}
		}
		return err
	}
	ProcessedMessages.WithLabelValues(c.queue).Inc()
	return nil
}
