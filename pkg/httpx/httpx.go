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
	req = req.WithContext(ctx)
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
