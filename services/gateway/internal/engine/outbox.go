package engine

import (
	"context"
	"database/sql"
	"encoding/json"
	"time"

	ckafka "github.com/confluentinc/confluent-kafka-go/kafka"
)

// Outbox provides methods to enqueue events for asynchronous publishing.
type Outbox struct {
	db *sql.DB
}

// NewOutbox returns a new Outbox bound to db.
func NewOutbox(db *sql.DB) *Outbox {
	return &Outbox{db: db}
}

// Enqueue stores an event payload for the given topic within the provided transaction.
func (o *Outbox) Enqueue(ctx context.Context, tx *sql.Tx, topic string, payload interface{}) error {
	data, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	_, err = tx.ExecContext(ctx, "INSERT INTO outbox (topic, payload) VALUES ($1,$2)", topic, data)
	return err
}

// OutboxPublisher periodically publishes pending outbox events to Kafka.
type OutboxPublisher struct {
	outbox   *Outbox
	producer *ckafka.Producer
	interval time.Duration
}

// NewOutboxPublisher creates an OutboxPublisher.
func NewOutboxPublisher(ob *Outbox, p *ckafka.Producer, interval time.Duration) *OutboxPublisher {
	if interval <= 0 {
		interval = time.Second
	}
	return &OutboxPublisher{outbox: ob, producer: p, interval: interval}
}

// Run starts the publishing loop until ctx is cancelled.
func (p *OutboxPublisher) Run(ctx context.Context) {
	ticker := time.NewTicker(p.interval)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			p.publish(ctx)
		}
	}
}

func (p *OutboxPublisher) publish(ctx context.Context) {
	rows, err := p.outbox.db.QueryContext(ctx, "SELECT id, topic, payload FROM outbox WHERE published_at IS NULL ORDER BY id LIMIT 100")
	if err != nil {
		return
	}
	defer rows.Close()
	for rows.Next() {
		var (
			id      int64
			topic   string
			payload []byte
		)
		if err := rows.Scan(&id, &topic, &payload); err != nil {
			continue
		}
		if err := p.producer.Produce(&ckafka.Message{TopicPartition: ckafka.TopicPartition{Topic: &topic, Partition: ckafka.PartitionAny}, Value: payload}, nil); err != nil {
			continue
		}
		_, _ = p.outbox.db.ExecContext(ctx, "UPDATE outbox SET published_at = NOW() WHERE id = $1", id)
	}
}
