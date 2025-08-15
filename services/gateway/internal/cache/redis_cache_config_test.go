package cache

import (
	"os"
	"testing"
)

func TestNewRedisCacheDefaults(t *testing.T) {
	os.Unsetenv("REDIS_HOST")
	os.Unsetenv("REDIS_PORT")
	os.Unsetenv("CACHE_TTL_SECONDS")

	c := NewRedisCache()
	opts := c.client.Options()
	if opts.Addr != "localhost:6379" {
		t.Fatalf("unexpected addr %s", opts.Addr)
	}
	if c.ttl.Seconds() != 300 {
		t.Fatalf("unexpected ttl %v", c.ttl)
	}
}

func TestNewRedisCacheFromEnv(t *testing.T) {
	os.Setenv("REDIS_HOST", "example.com")
	os.Setenv("REDIS_PORT", "1234")
	os.Setenv("CACHE_TTL_SECONDS", "42")

	c := NewRedisCache()
	opts := c.client.Options()
	if opts.Addr != "example.com:1234" {
		t.Fatalf("unexpected addr %s", opts.Addr)
	}
	if c.ttl.Seconds() != 42 {
		t.Fatalf("unexpected ttl %v", c.ttl)
	}
}
