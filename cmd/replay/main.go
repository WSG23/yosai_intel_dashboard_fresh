package main

import (
	"context"
	"flag"
	"io"
	"log"
	"time"

	ckafka "github.com/confluentinc/confluent-kafka-go/kafka"
)

// Consumer defines the subset of kafka consumer methods used by replay.
type Consumer interface {
	ReadMessage(timeout time.Duration) (*ckafka.Message, error)
	CommitMessage(*ckafka.Message) ([]ckafka.TopicPartition, error)
	Close() error
	Subscribe(topic string, rebalanceCb ckafka.RebalanceCb) error
}

// Producer defines the subset of kafka producer methods used by replay.
type Producer interface {
	Produce(msg *ckafka.Message, deliveryChan chan ckafka.Event) error
	Close()
}

func replay(ctx context.Context, c Consumer, p Producer, topic string) error {
	processed := make(map[string]struct{})
	for {
		select {
		case <-ctx.Done():
			return nil
		default:
		}
		msg, err := c.ReadMessage(-1)
		if err != nil {
			if err == io.EOF {
				return nil
			}
			continue
		}
		key := string(msg.Key)
		if _, ok := processed[key]; ok {
			_, _ = c.CommitMessage(msg)
			continue
		}
		processed[key] = struct{}{}
		msg.TopicPartition.Topic = &topic
		if err := p.Produce(msg, nil); err != nil {
			return err
		}
		_, _ = c.CommitMessage(msg)
	}
}

func main() {
	brokers := flag.String("brokers", "localhost:9092", "Kafka brokers")
	topic := flag.String("topic", "access-events", "Base topic name")
	flag.Parse()

	dlq := *topic + ".dlq"
	consumer, err := ckafka.NewConsumer(&ckafka.ConfigMap{
		"bootstrap.servers": *brokers,
		"group.id":          "replay-" + *topic,
		"auto.offset.reset": "earliest",
	})
	if err != nil {
		log.Fatalf("consumer init: %v", err)
	}
	defer consumer.Close()

	producer, err := ckafka.NewProducer(&ckafka.ConfigMap{
		"bootstrap.servers":  *brokers,
		"enable.idempotence": true,
		"acks":               "all",
		"transactional.id":   "replay-" + *topic,
	})
	if err != nil {
		log.Fatalf("producer init: %v", err)
	}
	defer func() {
		producer.Flush(5000)
		producer.Close()
	}()

	if err := consumer.Subscribe(dlq, nil); err != nil {
		log.Fatalf("subscribe: %v", err)
	}

	if err := replay(context.Background(), consumer, producer, *topic); err != nil {
		log.Fatalf("replay: %v", err)
	}
}
