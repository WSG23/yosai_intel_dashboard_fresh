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

type QueueClient struct {
	conn    *amqp.Connection
	channel *amqp.Channel
	mu      sync.RWMutex
}

type Task struct {
	ID         string          `json:"id"`
	Type       string          `json:"type"`
	Payload    json.RawMessage `json:"payload"`
	Priority   int             `json:"priority"`
	MaxRetries int             `json:"max_retries"`
	RetryCount int             `json:"retry_count"`
	CreatedAt  time.Time       `json:"created_at"`
}

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
		return nil, err
	}
	return &QueueClient{conn: conn, channel: ch}, nil
}

func (q *QueueClient) DeclareQueue(name string, durable bool) error {
	_, err := q.channel.QueueDeclare(name, durable, false, false, false, nil)
	return err
}

func (q *QueueClient) PublishTask(ctx context.Context, queue string, task *Task) error {
	body, err := json.Marshal(task)
	if err != nil {
		return err
	}
	return q.channel.PublishWithContext(ctx, "", queue, false, false, amqp.Publishing{
		ContentType:  "application/json",
		Body:         body,
		DeliveryMode: amqp.Persistent,
		Timestamp:    time.Now(),
	})
}

func (q *QueueClient) ConsumeQueue(ctx context.Context, queue string, handler func(context.Context, *Task) error) error {
	msgs, err := q.channel.Consume(queue, "", false, false, false, false, nil)
	if err != nil {
		return err
	}
	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case msg := <-msgs:
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
