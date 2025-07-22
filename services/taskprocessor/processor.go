package taskprocessor

import (
	"context"
	"encoding/json"

	"github.com/prometheus/client_golang/prometheus"

	"github.com/WSG23/queue/rabbitmq"
)

// TaskHandler defines a function invoked for each consumed task.
type TaskHandler func(context.Context, json.RawMessage) error

var (
	tasksProcessed = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "taskprocessor_tasks_processed_total",
			Help: "Number of tasks processed by the task processor",
		},
		[]string{"type", "status"},
	)
)

func init() {
	prometheus.MustRegister(tasksProcessed)
}

// TaskProcessor consumes tasks from a queue and dispatches them to handlers.
type TaskProcessor struct {
	queue    *rabbitmq.QueueClient
	handlers map[string]TaskHandler
}

// New creates a TaskProcessor using the provided queue URL.
func New(queueURL string) (*TaskProcessor, error) {
	q, err := rabbitmq.NewQueueClient(queueURL)
	if err != nil {
		return nil, err
	}
	return &TaskProcessor{queue: q, handlers: make(map[string]TaskHandler)}, nil
}

// RegisterHandler associates a handler with a task type.
func (tp *TaskProcessor) RegisterHandler(t string, h TaskHandler) {
	tp.handlers[t] = h
}

// Start begins consuming tasks from the given queue until ctx is cancelled.
func (tp *TaskProcessor) Start(ctx context.Context, queue string) error {
	return tp.queue.ConsumeQueue(ctx, queue, func(c context.Context, t *rabbitmq.Task) error {
		h, ok := tp.handlers[t.Type]
		if !ok {
			tasksProcessed.WithLabelValues(t.Type, "unhandled").Inc()
			return nil
		}
		if err := h(c, t.Payload); err != nil {
			tasksProcessed.WithLabelValues(t.Type, "error").Inc()
			return err
		}
		tasksProcessed.WithLabelValues(t.Type, "success").Inc()
		return nil
	})
}
