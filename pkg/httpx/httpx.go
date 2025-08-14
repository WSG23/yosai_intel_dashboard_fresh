package httpx

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/google/uuid"
)

// HTTPDoer is the subset of http.Client used by this package. It enables
// easy mocking in tests and constructor-based dependency injection.
type HTTPDoer interface {
	Do(*http.Request) (*http.Response, error)
}

// Client wraps an HTTPDoer to perform JSON requests.
type Client struct {
	httpClient HTTPDoer
}

// New creates a Client that uses the provided HTTPDoer.
func New(c HTTPDoer) *Client { return &Client{httpClient: c} }

// Default is the package level client used by DoJSON. It has a non-zero
// timeout to avoid hanging requests.
var Default = New(&http.Client{Timeout: 10 * time.Second})

// CorrelationIDKey is the context key used to store the correlation ID.
const CorrelationIDKey = "correlation_id"

// CorrelationIDHeader is the HTTP header carrying the correlation ID.
const CorrelationIDHeader = "X-Correlation-ID"

// WithCorrelationID returns a context containing a correlation ID. If the
// provided context already has one, it is reused.
func WithCorrelationID(ctx context.Context) (context.Context, string) {
	if v, ok := ctx.Value(CorrelationIDKey).(string); ok && v != "" {
		return ctx, v
	}
	id := uuid.NewString()
	return context.WithValue(ctx, CorrelationIDKey, id), id
}

// CorrelationIDFromContext extracts the correlation ID from context.
func CorrelationIDFromContext(ctx context.Context) string {
	if v, ok := ctx.Value(CorrelationIDKey).(string); ok {
		return v
	}
	return ""
}

// DoJSON executes the HTTP request using the client's HTTPDoer and decodes
// the JSON response body into dst. The provided context controls the request
// and will cancel the call if it is done.
func (c *Client) DoJSON(ctx context.Context, req *http.Request, dst any) (err error) {
	ctx, cid := WithCorrelationID(ctx)
	req = req.WithContext(ctx)
	if cid != "" {
		req.Header.Set(CorrelationIDHeader, cid)
	}
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("do request: %w", err)
	}
	defer func() {
		if cerr := resp.Body.Close(); cerr != nil && err == nil {
			err = fmt.Errorf("close body: %w", cerr)
		}
	}()

	if err := json.NewDecoder(resp.Body).Decode(dst); err != nil {
		return fmt.Errorf("decode json: %w", err)
	}
	return nil
}

// DoJSON executes the HTTP request using the Default client.
func DoJSON(ctx context.Context, req *http.Request, dst any) error {
	return Default.DoJSON(ctx, req, dst)
}
