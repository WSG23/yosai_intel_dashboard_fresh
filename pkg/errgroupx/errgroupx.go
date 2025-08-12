package errgroupx

import (
	"context"
	"fmt"
	"runtime/debug"

	"golang.org/x/sync/errgroup"
)

// Group wraps errgroup with a panic-recovering Go method.
type Group struct {
	ctx context.Context
	eg  *errgroup.Group
}

func WithContext(ctx context.Context) (*Group, context.Context) {
	eg, egctx := errgroup.WithContext(ctx)
	return &Group{ctx: egctx, eg: eg}, egctx
}

// Go starts a function and converts panics into errors joined on Wait.
func (g *Group) Go(fn func(ctx context.Context) error) {
	g.eg.Go(func() (err error) {
		defer func() {
			if r := recover(); r != nil {
				err = fmt.Errorf("panic: %v\n%s", r, debug.Stack())
			}
		}()
		return fn(g.ctx)
	})
}

// Wait waits for all goroutines and returns joined errors (if multiple).
func (g *Group) Wait() error {
	if err := g.eg.Wait(); err != nil {
		return err
	}
	return nil
}
