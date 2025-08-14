package httpx

import "time"

// Config holds timeout and backoff settings for HTTP requests.
type Config struct {
	Timeout time.Duration
	Backoff time.Duration
	Retries int
}

// DefaultConfig provides sane defaults for HTTP clients.
func DefaultConfig() Config {
	return Config{
		Timeout: 10 * time.Second,
		Backoff: 50 * time.Millisecond,
		Retries: 3,
	}
}
