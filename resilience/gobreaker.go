package resilience

import "github.com/sony/gobreaker"

// NewGoBreaker returns a gobreaker.CircuitBreaker instrumented with
// state transition metrics using breakerState from circuit_breaker.go.
func NewGoBreaker(settings gobreaker.Settings) *gobreaker.CircuitBreaker {
	name := settings.Name
	prev := settings.OnStateChange
	settings.OnStateChange = func(_ string, from, to gobreaker.State) {
		switch to {
		case gobreaker.StateOpen:
			breakerState.WithLabelValues(name, "open").Inc()
		case gobreaker.StateHalfOpen:
			breakerState.WithLabelValues(name, "half_open").Inc()
		case gobreaker.StateClosed:
			breakerState.WithLabelValues(name, "closed").Inc()
		}
		if prev != nil {
			prev(name, from, to)
		}
	}
	return gobreaker.NewCircuitBreaker(settings)
}
