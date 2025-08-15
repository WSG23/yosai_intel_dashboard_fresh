package kafka

import (
    "context"
    "errors"
    "sync/atomic"
    "testing"

    ckafka "github.com/confluentinc/confluent-kafka-go/kafka"
)

type mockClient struct {
    subscribeErr error
    messages     []*ckafka.Message
    commitCount  int32
}

func (m *mockClient) SubscribeTopics([]string, ckafka.RebalanceCb) error { return m.subscribeErr }
func (m *mockClient) ReadMessage(int) (*ckafka.Message, error) {
    if len(m.messages) == 0 {
        return nil, ckafka.NewError(ckafka.ErrTimedOut, "timeout", false)
    }
    msg := m.messages[0]
    m.messages = m.messages[1:]
    return msg, nil
}
func (m *mockClient) CommitMessage(*ckafka.Message) ([]ckafka.TopicPartition, error) {
    atomic.AddInt32(&m.commitCount, 1)
    return nil, nil
}
func (m *mockClient) Close() {}

func TestNewConsumerError(t *testing.T) {
    old := newClient
    newClient = func(cfg *ckafka.ConfigMap) (kafkaClient, error) { return nil, errors.New("boom") }
    defer func() { newClient = old }()
    if _, err := NewConsumer("b", "g"); err == nil {
        t.Fatal("expected error")
    }
}

func TestConsumeSubscribeError(t *testing.T) {
    mc := &mockClient{subscribeErr: errors.New("bad")}
    c := &Consumer{c: mc}
    if err := c.Consume(context.Background(), []string{"t"}, func(context.Context, *ckafka.Message) error { return nil }); err == nil {
        t.Fatal("expected error")
    }
}

func TestConsumeProcesses(t *testing.T) {
    mc := &mockClient{messages: []*ckafka.Message{{Key: []byte("k1")}, {Key: []byte("k1")}}}
    c := &Consumer{c: mc}
    ctx, cancel := context.WithCancel(context.Background())
    var processed int32
    errCh := make(chan error, 1)
    go func() {
        errCh <- c.Consume(ctx, []string{"t"}, func(ctx context.Context, m *ckafka.Message) error {
            atomic.AddInt32(&processed, 1)
            cancel()
            return nil
        })
    }()
    if err := <-errCh; err != context.Canceled {
        t.Fatalf("expected context canceled, got %v", err)
    }
    if processed != 1 {
        t.Fatalf("expected 1 processed, got %d", processed)
    }
    if mc.commitCount != 1 {
        t.Fatalf("expected commit, got %d", mc.commitCount)
    }
}

