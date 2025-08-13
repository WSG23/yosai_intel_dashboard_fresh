package logging

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
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
}

// NewAuditLogger creates an AuditLogger. The Elasticsearch endpoint can be
// provided via the AUDIT_ELASTIC_URL environment variable. If not set, the
// logger will be disabled.
func NewAuditLogger() *AuditLogger {
	ep := os.Getenv("AUDIT_ELASTIC_URL")
	if ep == "" {
		return &AuditLogger{}
	}
	return &AuditLogger{
		endpoint: ep,
		index:    "audit", // default index
		client:   &http.Client{Timeout: 2 * time.Second},
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
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(data))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := l.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	io.Copy(io.Discard, resp.Body)
	return nil
}
