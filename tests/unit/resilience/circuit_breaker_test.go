package test

import (
	"context"
	"testing"
	"time"

	cb "github.com/WSG23/resilience"
)

func TestStateTransitions(t *testing.T) {
	breaker := cb.New("test", 2, 10*time.Millisecond, 10, 0.8)

	// two failures trigger open
	if err := breaker.Execute(context.Background(), func(ctx context.Context) error { return context.Canceled }, nil); err == nil {
		t.Fatal("expected error")
	}
	if breaker.Allows() != true {
		t.Fatal("should allow after first failure")
	}
	if err := breaker.Execute(context.Background(), func(ctx context.Context) error { return context.Canceled }, nil); err == nil {
		t.Fatal("expected error")
	}
	if breaker.Allows() {
		t.Fatal("breaker should be open")
	}

	time.Sleep(15 * time.Millisecond)
	if !breaker.Allows() {
		t.Fatal("expected half-open after timeout")
	}
	if err := breaker.Execute(context.Background(), func(ctx context.Context) error { return nil }, nil); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !breaker.Allows() {
		t.Fatal("breaker should be closed after success")
	}
}

func TestAdaptiveAdjustments(t *testing.T) {
	breaker := cb.New("adaptive", 3, 10*time.Millisecond, 4, 0.75)

	// 3 successes, 1 failure -> rate 0.75 meets slo -> no change
	for i := 0; i < 3; i++ {
		breaker.Execute(context.Background(), func(ctx context.Context) error { return nil }, nil)
	}
	breaker.Execute(context.Background(), func(ctx context.Context) error { return context.Canceled }, nil)
	if breaker.Allows() == false {
		t.Fatal("breaker should remain closed")
	}
	// 4 failures -> below slo -> threshold should decrease
	for i := 0; i < 4; i++ {
		breaker.Execute(context.Background(), func(ctx context.Context) error { return context.Canceled }, nil)
	}
	if breaker.Allows() {
		t.Fatal("breaker should be open after failures")
	}
	if breaker.Execute(context.Background(), func(ctx context.Context) error { return nil }, func(ctx context.Context) error { return nil }) != nil {
		t.Fatal("fallback should succeed")
	}
}

func TestFallbackWhenOpen(t *testing.T) {
	breaker := cb.New("fallback", 1, 10*time.Millisecond, 1, 0.9)
	breaker.Execute(context.Background(), func(ctx context.Context) error { return context.Canceled }, nil)
	if breaker.Allows() {
		t.Fatal("breaker should be open")
	}
	called := false
	err := breaker.Execute(context.Background(), func(ctx context.Context) error { return nil }, func(ctx context.Context) error {
		called = true
		return nil
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !called {
		t.Fatal("fallback was not executed")
	}
}
