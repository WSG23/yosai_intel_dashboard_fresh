package cache

import (
	"context"
	"os"
	"testing"
	"time"

	"github.com/alicebob/miniredis/v2"
)

func TestRedisCacheSetGet(t *testing.T) {
	srv, err := miniredis.Run()
	if err != nil {
		t.Fatalf("failed to start miniredis: %v", err)
	}
	defer srv.Close()

	os.Setenv("REDIS_HOST", srv.Host())
	os.Setenv("REDIS_PORT", srv.Port())
	os.Setenv("CACHE_TTL_SECONDS", "1")

	c := NewRedisCache()

	dec := Decision{PersonID: "p", DoorID: "d", Decision: "Granted"}
	if err := c.SetDecision(context.Background(), dec); err != nil {
		t.Fatalf("set: %v", err)
	}

	got, err := c.GetDecision(context.Background(), "p", "d")
	if err != nil {
		t.Fatalf("get: %v", err)
	}
	if got == nil || got.Decision != "Granted" {
		t.Fatalf("unexpected decision: %+v", got)
	}

       // ensure TTL expires
       srv.FastForward(2 * time.Second)
       expired, err := c.GetDecision(context.Background(), "p", "d")
       if err != nil {
               t.Fatalf("get after ttl: %v", err)
       }
       if expired != nil {
               t.Fatalf("expected nil after ttl, got %+v", expired)
       }
}

func TestRedisCacheMissReturnsNil(t *testing.T) {
	srv, err := miniredis.Run()
	if err != nil {
		t.Fatalf("failed to start miniredis: %v", err)
	}
	defer srv.Close()

	os.Setenv("REDIS_HOST", srv.Host())
	os.Setenv("REDIS_PORT", srv.Port())
	os.Setenv("CACHE_TTL_SECONDS", "1")

       c := NewRedisCache()
       got, err := c.GetDecision(context.Background(), "missing", "door")
       if err != nil {
               t.Fatalf("get: %v", err)
       }
       if got != nil {
               t.Fatalf("expected nil decision, got %+v", got)
       }
}
