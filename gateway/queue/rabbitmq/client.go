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

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/trace"
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

// amqpHeadersCarrier adapts amqp.Table to a propagation carrier.
// Only string values are used for trace propagation.
type amqpHeadersCarrier amqp.Table

func (c amqpHeadersCarrier) Get(key string) string {
	if v, ok := amqp.Table(c)[key]; ok {
		if s, ok := v.(string); ok {
			return s
		}
	}
	return ""
}

func (c amqpHeadersCarrier) Set(key, val string) {
	amqp.Table(c)[key] = val
}

func (c amqpHeadersCarrier) Keys() []string {
	keys := make([]string, 0, len(amqp.Table(c)))
	for k := range amqp.Table(c) {
		keys = append(keys, k)
	}
	return keys
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
	ctx, span := otel.Tracer("queue").Start(ctx, "rabbitmq.publish", trace.WithAttributes(attribute.String("queue", queue)))
	defer span.End()
	body, err := json.Marshal(task)
	if err != nil {
		span.RecordError(err)
		return err
	}
	headers := amqp.Table{}
	otel.GetTextMapPropagator().Inject(ctx, amqpHeadersCarrier(headers))
	err = q.channel.PublishWithContext(ctx, "", queue, false, false, amqp.Publishing{
		ContentType:  "application/json",
		Body:         body,
		DeliveryMode: amqp.Persistent,
		Timestamp:    time.Now(),
		Headers:      headers,
	})
	if err != nil {
		span.RecordError(err)
	}
	return err
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
			mctx := otel.GetTextMapPropagator().Extract(ctx, amqpHeadersCarrier(msg.Headers))
			cctx, span := otel.Tracer("queue").Start(mctx, "rabbitmq.consume", trace.WithAttributes(attribute.String("queue", queue)))
			if err := handler(cctx, &t); err != nil {
				span.RecordError(err)
				msg.Nack(false, true)
			} else {
				msg.Ack(false)
			}
			span.End()
		}
	}
}
