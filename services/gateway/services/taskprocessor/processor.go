package taskprocessor

import (
	"context"
	"encoding/json"

	"github.com/prometheus/client_golang/prometheus"

	"github.com/WSG23/yosai-gateway/queue/rabbitmq"
)

type TaskHandler func(context.Context, json.RawMessage) error

type TaskProcessor struct {
	queue    *rabbitmq.QueueClient
	handlers map[string]TaskHandler
}

type TaskMetrics struct {
	processed *prometheus.CounterVec
}

func New(queueURL string) (*TaskProcessor, error) {
	q, err := rabbitmq.NewQueueClient(queueURL)
	if err != nil {
		return nil, err
	}
	return &TaskProcessor{queue: q, handlers: make(map[string]TaskHandler)}, nil
}

func (tp *TaskProcessor) RegisterHandler(t string, h TaskHandler) {
	tp.handlers[t] = h
}

func (tp *TaskProcessor) Start(ctx context.Context, queue string) error {
	return tp.queue.ConsumeQueue(ctx, queue, func(c context.Context, t *rabbitmq.Task) error {
		h, ok := tp.handlers[t.Type]
		if !ok {
			return nil
		}
		return h(c, t.Payload)
	})
}
