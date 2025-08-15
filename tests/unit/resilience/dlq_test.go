package test

import (
        "context"
        "errors"
        "testing"

	q "github.com/WSG23/queue"
	"github.com/WSG23/queue/rabbitmq"
	"github.com/prometheus/client_golang/prometheus/testutil"
)

type mockProducer struct {
	tasks []*rabbitmq.Task
}

func (m *mockProducer) Publish(ctx context.Context, queue string, task *rabbitmq.Task) error {
	m.tasks = append(m.tasks, task)
	return nil
}

func TestDLQProducer(t *testing.T) {
	mp := &mockProducer{}
	c := q.NewConsumer("jobs", "jobs-dlq", mp)
	msg := []byte(`{"id":"1","max_retries":1}`)
	handler := func(ctx context.Context, task *rabbitmq.Task) error {
		return errors.New("fail")
	}
	if err := c.Process(context.Background(), msg, handler); err == nil {
		t.Fatal("expected error")
	}
	if len(mp.tasks) != 1 {
		t.Fatalf("expected 1 DLQ message, got %d", len(mp.tasks))
	}
	if v := testutil.ToFloat64(q.DLQMessages.WithLabelValues("jobs")); v != 1 {
		t.Fatalf("expected metric 1, got %v", v)
	}
}

func TestConsumerIdempotency(t *testing.T) {
	mp := &mockProducer{}
	c := q.NewConsumer("jobs", "jobs-dlq", mp)
	count := 0
	handler := func(ctx context.Context, task *rabbitmq.Task) error {
		count++
		return nil
	}
	msg := []byte(`{"id":"42"}`)
	if err := c.Process(context.Background(), msg, handler); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if err := c.Process(context.Background(), msg, handler); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if count != 1 {
		t.Fatalf("handler called %d times, want 1", count)
	}
}

func TestDLQInvalidMessage(t *testing.T) {
        mp := &mockProducer{}
        c := q.NewConsumer("jobs", "jobs-dlq", mp)
        if err := c.Process(context.Background(), []byte("not-json"), func(context.Context, *rabbitmq.Task) error { return nil }); err == nil {
                t.Fatal("expected unmarshal error")
        }
        if len(mp.tasks) != 1 {
                t.Fatalf("expected 1 DLQ message, got %d", len(mp.tasks))
        }
        if mp.tasks[0].ID == "" {
                t.Fatal("dlq message missing id")
        }
}
