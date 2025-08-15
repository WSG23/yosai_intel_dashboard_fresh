package logging

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"math/rand"
	"net/http"
	"os"
	"time"

	"github.com/sony/gobreaker"

	"github.com/WSG23/resilience"
)

// AuditLog represents a structured audit entry.
type AuditLog struct {
	User      string    `json:"user"`
	Timestamp time.Time `json:"timestamp"`
	Action    string    `json:"action"`
	Outcome   string    `json:"outcome"`
}

// AuditLogger sends audit logs to a centralized store like Elasticsearch.
type AuditLogger struct {
	endpoint string
	index    string
	client   *http.Client
	breaker  *gobreaker.CircuitBreaker
}

// NewAuditLogger creates an AuditLogger. The Elasticsearch endpoint can be
// provided via the AUDIT_ELASTIC_URL environment variable. If not set, the
// logger will be disabled.
func NewAuditLogger() *AuditLogger {
	ep := os.Getenv("AUDIT_ELASTIC_URL")
	if ep == "" {
		return &AuditLogger{}
	}
	settings := gobreaker.Settings{
		Name:        "audit-logger",
		Timeout:     time.Second + time.Duration(rand.Intn(1000))*time.Millisecond,
		ReadyToTrip: func(c gobreaker.Counts) bool { return c.ConsecutiveFailures >= 3 },
	}
	return &AuditLogger{
		endpoint: ep,
		index:    "audit", // default index
		client:   &http.Client{},
		breaker:  resilience.NewGoBreaker("audit-logger", settings),
	}
}

// Log indexes the provided entry. Errors are returned but can be ignored by
// callers if persistence failures shouldn't block requests.
func (l *AuditLogger) Log(ctx context.Context, entry AuditLog) error {
	if l == nil || l.client == nil || l.endpoint == "" {
		return nil
	}
	data, err := json.Marshal(entry)
	if err != nil {
		return err
	}
	url := fmt.Sprintf("%s/%s/_doc", l.endpoint, l.index)
	ctx, cancel := context.WithTimeout(ctx, 20*time.Millisecond)
	defer cancel()
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(data))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	_, err = l.breaker.Execute(func() (interface{}, error) {
		resp, err := l.client.Do(req)
		if err != nil {
			return nil, err
		}
		defer resp.Body.Close()
		if resp.StatusCode >= 500 {
			return nil, fmt.Errorf("status %d", resp.StatusCode)
		}
		io.Copy(io.Discard, resp.Body)
		return nil, nil
	})
	return err
}
