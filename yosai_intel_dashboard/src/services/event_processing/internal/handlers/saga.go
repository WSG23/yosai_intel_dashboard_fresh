package handlers

import "context"

type sagaStep struct {
	action     func(context.Context) error
	compensate func(context.Context) error
}

type Saga struct {
	steps []sagaStep
}

func NewSaga() *Saga { return &Saga{} }

// AddStep appends a transactional step with its compensation.
func (s *Saga) AddStep(action, compensate func(context.Context) error) {
	s.steps = append(s.steps, sagaStep{action: action, compensate: compensate})
}

// Execute runs all steps. On failure already executed steps are compensated in reverse order.
func (s *Saga) Execute(ctx context.Context) error {
	executed := []sagaStep{}
	for _, step := range s.steps {
		if err := step.action(ctx); err != nil {
			for i := len(executed) - 1; i >= 0; i-- {
				_ = executed[i].compensate(ctx)
			}
			return err
		}
		executed = append(executed, step)
	}
	return nil
}
