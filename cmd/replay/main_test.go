package main

import (
        "context"
        "io"
        "testing"
        "time"

        ckafka "github.com/confluentinc/confluent-kafka-go/kafka"
)

type mockConsumer struct {
        msgs []*ckafka.Message
        idx  int
}

func (m *mockConsumer) ReadMessage(timeout time.Duration) (*ckafka.Message, error) {
        if m.idx >= len(m.msgs) {
                return nil, io.EOF
        }
        msg := m.msgs[m.idx]
        m.idx++
        return msg, nil
}

func (m *mockConsumer) CommitMessage(*ckafka.Message) ([]ckafka.TopicPartition, error) { return nil, nil }
func (m *mockConsumer) Close() error                                        { return nil }
func (m *mockConsumer) Subscribe(topic string, rb ckafka.RebalanceCb) error { return nil }

type mockProducer struct {
        msgs []*ckafka.Message
}

func (m *mockProducer) Produce(msg *ckafka.Message, deliveryChan chan ckafka.Event) error {
        m.msgs = append(m.msgs, msg)
        return nil
}

func (m *mockProducer) Close() {}

func TestReplayIdempotency(t *testing.T) {
        msgs := []*ckafka.Message{
                {Key: []byte("id1"), Value: []byte("v1")},
                {Key: []byte("id1"), Value: []byte("v1-dup")},
                {Key: []byte("id2"), Value: []byte("v2")},
        }
        c := &mockConsumer{msgs: msgs}
        p := &mockProducer{}
        if err := replay(context.Background(), c, p, "access-events"); err != nil {
                t.Fatalf("replay failed: %v", err)
        }
        if len(p.msgs) != 2 {
                t.Fatalf("expected 2 unique messages, got %d", len(p.msgs))
        }
        if string(p.msgs[0].Key) != "id1" || string(p.msgs[1].Key) != "id2" {
                t.Fatalf("unexpected message keys: %v %v", string(p.msgs[0].Key), string(p.msgs[1].Key))
        }
}

