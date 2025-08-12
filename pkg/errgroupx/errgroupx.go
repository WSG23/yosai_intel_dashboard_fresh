package errgroupx

import (
	"context"
	"errors"
	"fmt"
	"sync"
)

// Group is a collection of goroutines working on subtasks that are part of
// the same overall task.
type Group struct {
	cancel func(error)
	ctx    context.Context

	wg sync.WaitGroup

	mu   sync.Mutex
	errs []error
}

// WithContext returns a new Group and an associated Context derived from ctx.
// The derived Context is canceled the first time a function passed to Go
// returns a non-nil error or panics.
func WithContext(ctx context.Context) (*Group, context.Context) {
	ctx, cancel := context.WithCancelCause(ctx)
	g := &Group{cancel: cancel, ctx: ctx}
	return g, ctx
}

// Go calls the given function in a new goroutine.
func (g *Group) Go(fn func(context.Context) error) {
	g.wg.Add(1)
	go func() {
		defer g.wg.Done()
		if err := g.run(fn); err != nil {
			g.mu.Lock()
			g.errs = append(g.errs, err)
			g.mu.Unlock()
		}
	}()
}

func (g *Group) run(fn func(context.Context) error) (err error) {
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("panic: %v", r)
		}
		if err != nil {
			g.cancel(err)
		}
	}()
	return fn(g.ctx)
}

// Wait blocks until all function calls from the Go method have returned, then
// returns the combined error.
func (g *Group) Wait() error {
	g.wg.Wait()
	g.cancel(nil)

	g.mu.Lock()
	defer g.mu.Unlock()
	if len(g.errs) == 0 {
		return nil
	}
	return errors.Join(g.errs...)
}
