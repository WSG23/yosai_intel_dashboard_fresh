package queue

import (
        "context"
        "encoding/json"
        "sync"

        "github.com/google/uuid"
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

func init() {
	prometheus.MustRegister(DLQMessages)
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
                        _ = c.p.Publish(ctx, c.dlq, &rabbitmq.Task{ID: uuid.NewString(), Payload: msg})
                }
                return err
        }
	if _, ok := c.processed.LoadOrStore(t.ID, struct{}{}); ok {
		return nil
	}
	if err := handler(ctx, &t); err != nil {
		t.RetryCount++
		if t.MaxRetries > 0 && t.RetryCount >= t.MaxRetries {
			DLQMessages.WithLabelValues(c.queue).Inc()
			if c.p != nil {
				_ = c.p.Publish(ctx, c.dlq, &t)
			}
		}
		return err
	}
	return nil
}
