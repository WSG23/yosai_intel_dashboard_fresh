package httpx

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"

	cb "github.com/WSG23/resilience"
	"github.com/sony/gobreaker"
)

// HTTPDoer is the subset of http.Client used by this package. It enables
// easy mocking in tests and constructor-based dependency injection.
type HTTPDoer interface {
	Do(*http.Request) (*http.Response, error)
}

// Client wraps an HTTPDoer to perform JSON requests.
type Client struct {
	httpClient HTTPDoer
	breaker    *gobreaker.CircuitBreaker
	cfg        Config
}

// New creates a Client that uses the provided HTTPDoer with default settings.
func New(c HTTPDoer) *Client {
	return NewWithConfig(c, DefaultConfig(), nil)
}

// NewWithConfig allows providing a configuration and custom breaker.
func NewWithConfig(c HTTPDoer, cfg Config, b *gobreaker.CircuitBreaker) *Client {
	if b == nil {
		b = cb.NewGoBreaker("httpx", gobreaker.Settings{})
	}
	return &Client{httpClient: c, breaker: b, cfg: cfg}
}

// Default is the package level client used by DoJSON. It uses DefaultConfig.
var Default = NewWithConfig(&http.Client{Timeout: DefaultConfig().Timeout}, DefaultConfig(), nil)

// NewTLSClient creates a Client using certificates for mTLS.
func NewTLSClient(certFile, keyFile, caFile string) (*Client, error) {
	cfg := &tls.Config{}
	if caFile != "" {
		ca, err := os.ReadFile(caFile)
		if err != nil {
			return nil, err
		}
		pool := x509.NewCertPool()
		if !pool.AppendCertsFromPEM(ca) {
			return nil, fmt.Errorf("append ca cert")
		}
		cfg.RootCAs = pool
	}
	if certFile != "" && keyFile != "" {
		cert, err := tls.LoadX509KeyPair(certFile, keyFile)
		if err != nil {
			return nil, err
		}
		cfg.Certificates = []tls.Certificate{cert}
	}
	tr := &http.Transport{TLSClientConfig: cfg}
	return New(&http.Client{Transport: tr, Timeout: 10 * time.Second}), nil
}

// DoJSON executes the HTTP request using the client's HTTPDoer and decodes
// the JSON response body into dst. The provided context controls the request
// and will cancel the call if it is done.
func (c *Client) DoJSON(ctx context.Context, req *http.Request, dst any) (err error) {
	ctx, cid := EnsureCorrelationID(ctx)
	req = req.WithContext(ctx)
	if req.Header.Get(CorrelationIDHeader) == "" {
		req.Header.Set(CorrelationIDHeader, cid)
	}
	var resp *http.Response
	backoff := c.cfg.Backoff
	for attempt := 0; ; attempt++ {
		_, err = c.breaker.Execute(func() (interface{}, error) {
			var e error
			resp, e = c.httpClient.Do(req)
			return nil, e
		})
		if err == nil || attempt >= c.cfg.Retries {
			break
		}
		time.Sleep(backoff)
		backoff *= 2
	}
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
