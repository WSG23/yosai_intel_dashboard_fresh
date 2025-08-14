package rabbitmq

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"os"
	"sync"
	"time"

	amqp "github.com/rabbitmq/amqp091-go"
)

// QueueClient wraps an AMQP connection and channel.
type QueueClient struct {
	conn    *amqp.Connection
	channel *amqp.Channel
	mu      sync.RWMutex
}

// Task represents a work item sent through the queue.
type Task struct {
	ID         string          `json:"id"`
	Type       string          `json:"type"`
	Payload    json.RawMessage `json:"payload"`
	Priority   uint8           `json:"priority"`
	Delay      int64           `json:"delay"`
	MaxRetries int             `json:"max_retries"`
	RetryCount int             `json:"retry_count"`
	CreatedAt  time.Time       `json:"created_at"`
}

// NewQueueClient establishes a new AMQP connection.
func NewQueueClient(url string) (*QueueClient, error) {
	tlsCert := os.Getenv("TLS_CERT_FILE")
	tlsKey := os.Getenv("TLS_KEY_FILE")
	tlsCA := os.Getenv("TLS_CA_FILE")
	var conn *amqp.Connection
	var err error
	if tlsCert != "" && tlsKey != "" {
		cfg := &tls.Config{}
		if tlsCA != "" {
			ca, err2 := os.ReadFile(tlsCA)
			if err2 == nil {
				pool := x509.NewCertPool()
				if pool.AppendCertsFromPEM(ca) {
					cfg.RootCAs = pool
				}
			}
		}
		cert, err2 := tls.LoadX509KeyPair(tlsCert, tlsKey)
		if err2 == nil {
			cfg.Certificates = []tls.Certificate{cert}
		}
		conn, err = amqp.DialTLS(url, cfg)
	} else {
		conn, err = amqp.Dial(url)
	}
	if err != nil {
		return nil, err
	}
	ch, err := conn.Channel()
	if err != nil {
		conn.Close()
		return nil, err
	}
	return &QueueClient{conn: conn, channel: ch}, nil
}

// DeclareQueue ensures a queue exists with optional dead-letter routing and priority support.
func (q *QueueClient) DeclareQueue(name string, durable bool, deadLetter string, maxPriority int) error {
	args := amqp.Table{}
	if deadLetter != "" {
		args["x-dead-letter-exchange"] = ""
		args["x-dead-letter-routing-key"] = deadLetter
	}
	if maxPriority > 0 {
		args["x-max-priority"] = int32(maxPriority)
	}
	_, err := q.channel.QueueDeclare(name, durable, false, false, false, args)
	return err
}

// PublishTask publishes a Task to the queue with optional delay and priority.
func (q *QueueClient) PublishTask(ctx context.Context, queue string, task *Task) error {
	body, err := json.Marshal(task)
	if err != nil {
		return err
	}
	headers := amqp.Table{}
	if task.Delay > 0 {
		headers["x-delay"] = task.Delay
	}
	return q.channel.PublishWithContext(ctx, "", queue, false, false, amqp.Publishing{
		ContentType:  "application/json",
		Body:         body,
		DeliveryMode: amqp.Persistent,
		Priority:     task.Priority,
		Timestamp:    time.Now(),
		Headers:      headers,
	})
}

// ConsumeQueue consumes messages from queue until ctx is cancelled.
func (q *QueueClient) ConsumeQueue(ctx context.Context, queue string, handler func(context.Context, *Task) error) error {
	msgs, err := q.channel.Consume(queue, "", false, false, false, false, nil)
	if err != nil {
		return err
	}
	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case msg, ok := <-msgs:
			if !ok {
				return nil
			}
			var t Task
			if err := json.Unmarshal(msg.Body, &t); err != nil {
				msg.Nack(false, false)
				continue
			}
			if err := handler(ctx, &t); err != nil {
				msg.Nack(false, true)
			} else {
				msg.Ack(false)
			}
		}
	}
}

// Close shuts down the underlying AMQP connection.
func (q *QueueClient) Close() error {
	q.mu.Lock()
	defer q.mu.Unlock()
	if q.channel != nil {
		_ = q.channel.Close()
	}
	if q.conn != nil {
		return q.conn.Close()
	}
	return nil
}
