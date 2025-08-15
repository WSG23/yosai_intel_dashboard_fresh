package proxy

import (
	"net/http"

	"github.com/WSG23/yosai-gateway/tracing"
	"go.opentelemetry.io/otel/propagation"
)

// tracingTransport wraps a RoundTripper and injects
// OpenTelemetry trace headers into each outgoing request.
type tracingTransport struct {
	base http.RoundTripper
}

func (t *tracingTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	tracing.PropagateContext(req.Context(), propagation.HeaderCarrier(req.Header))
	return t.base.RoundTrip(req)
}

// newTracingTransport returns a transport that injects trace headers.
func newTracingTransport(rt http.RoundTripper) http.RoundTripper {
	if rt == nil {
		rt = http.DefaultTransport
	}
	return &tracingTransport{base: rt}
}
