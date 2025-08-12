package errgroupx

import (
    "context"
    "errors"
    "testing"
)

func TestPanicCaptured(t *testing.T) {
    g, _ := WithContext(context.Background())
    g.Go(func(ctx context.Context) error {
        panic("boom")
    })
    if err := g.Wait(); err == nil {
        t.Fatal("expected panic to be converted to error")
    }
}

func TestErrorJoin(t *testing.T) {
    g, _ := WithContext(context.Background())
    g.Go(func(ctx context.Context) error { return errors.New("a") })
    g.Go(func(ctx context.Context) error { return nil })
    if err := g.Wait(); err == nil {
        t.Fatal("expected error")
    }
}

