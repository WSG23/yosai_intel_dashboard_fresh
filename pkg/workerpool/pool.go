package workerpool

import "context"

// Pool executes tasks with bounded concurrency.
type Pool struct {
	sem chan struct{}
}

func New(n int) *Pool { return &Pool{sem: make(chan struct{}, n)} }

func (p *Pool) Go(ctx context.Context, fn func(ctx context.Context)) {
	select {
	case p.sem <- struct{}{}:
		go func() {
			defer func() { <-p.sem }()
			fn(ctx)
		}()
	case <-ctx.Done():
		return
	}
}
