// Package loadbalancer provides advanced backend selection.
package loadbalancer

import (
	"context"
	"net/http"
	"net/url"
	"sync"
	"time"
)

// backend holds metrics about a single backend service.
type backend struct {
	url     *url.URL
	mu      sync.Mutex
	success int64
	failure int64
	latency time.Duration
}

// record updates the backend metrics with the result of a single request.
func (b *backend) record(success bool, latency time.Duration) {
	b.mu.Lock()
	defer b.mu.Unlock()
	if success {
		b.success++
	} else {
		b.failure++
	}
	if b.latency == 0 {
		b.latency = latency
	} else {
		// Exponential moving average to smooth latencies
		const weight = 0.8
		b.latency = time.Duration(float64(b.latency)*weight + float64(latency)*(1-weight))
	}
}

// metrics returns the current success rate and average latency.
func (b *backend) metrics() (rate float64, lat time.Duration) {
	b.mu.Lock()
	defer b.mu.Unlock()
	total := b.success + b.failure
	if total == 0 {
		rate = 1
	} else {
		rate = float64(b.success) / float64(total)
	}
	lat = b.latency
	if lat == 0 {
		lat = time.Millisecond
	}
	return
}

// AdvancedLoadBalancer selects the best backend based on success rate and latency.
type AdvancedLoadBalancer struct {
	backends []*backend
}

// NewAdvanced creates a new load balancer from the provided backend URLs.
func NewAdvanced(urls []*url.URL) *AdvancedLoadBalancer {
	bks := make([]*backend, 0, len(urls))
	for _, u := range urls {
		bks = append(bks, &backend{url: u})
	}
	return &AdvancedLoadBalancer{backends: bks}
}

// Next returns the backend that should handle the next request.
func (lb *AdvancedLoadBalancer) Next() *backend {
	if len(lb.backends) == 0 {
		return nil
	}
	best := lb.backends[0]
	bestRate, bestLat := best.metrics()
	for _, b := range lb.backends[1:] {
		r, l := b.metrics()
		if r > bestRate || (r == bestRate && l < bestLat) {
			best = b
			bestRate = r
			bestLat = l
		}
	}
	return best
}

// Report updates metrics for a backend after a request is completed.
func (lb *AdvancedLoadBalancer) Report(b *backend, success bool, lat time.Duration) {
	if b == nil {
		return
	}
	b.record(success, lat)
}

// URL returns the URL of the backend.
func (b *backend) URL() *url.URL { return b.url }

// context keys for storing backend info
type ctxKey string

const (
	backendKey ctxKey = "lb_backend"
	startKey   ctxKey = "lb_start"
)

// Director selects a backend for the incoming request and rewrites the URL.
func (lb *AdvancedLoadBalancer) Director(req *http.Request) {
	b := lb.Next()
	if b == nil {
		return
	}
	ctx := context.WithValue(req.Context(), backendKey, b)
	ctx = context.WithValue(ctx, startKey, time.Now())
	req.URL.Scheme = b.url.Scheme
	req.URL.Host = b.url.Host
	req.Host = b.url.Host
	*req = *req.WithContext(ctx)
}

// ModifyResponse records successful requests to a backend.
func (lb *AdvancedLoadBalancer) ModifyResponse(resp *http.Response) error {
	b, _ := resp.Request.Context().Value(backendKey).(*backend)
	start, _ := resp.Request.Context().Value(startKey).(time.Time)
	success := resp.StatusCode < http.StatusInternalServerError
	lb.Report(b, success, time.Since(start))
	return nil
}

// ErrorHandler records failed requests and returns a bad gateway response.
func (lb *AdvancedLoadBalancer) ErrorHandler(w http.ResponseWriter, r *http.Request, err error) {
	b, _ := r.Context().Value(backendKey).(*backend)
	start, _ := r.Context().Value(startKey).(time.Time)
	lb.Report(b, false, time.Since(start))
	http.Error(w, err.Error(), http.StatusBadGateway)
}
