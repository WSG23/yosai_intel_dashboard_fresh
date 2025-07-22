package resilience

import (
    "context"
    "errors"
    "sync"
    "time"

    "github.com/prometheus/client_golang/prometheus"
)

var (
    breakerState = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "circuit_breaker_state_transitions_total",
            Help: "Count of circuit breaker state transitions",
        },
        []string{"name", "state"},
    )
)

func init() {
    prometheus.MustRegister(breakerState)
}

// ErrOpen is returned when the circuit is open and no fallback is provided.
var ErrOpen = errors.New("circuit breaker is open")

type State int

const (
    Closed State = iota
    Open
    HalfOpen
)

// CircuitBreaker implements an adaptive circuit breaker.
type CircuitBreaker struct {
    mu      sync.Mutex
    state   State

    failureThreshold      int
    baseFailureThreshold  int
    recoveryTimeout       time.Duration
    baseRecoveryTimeout   time.Duration
    window                int
    slo                   float64

    failures int
    successes int
    openedAt time.Time
    name     string
}

// New creates an adaptive circuit breaker.
func New(name string, failureThreshold int, recoveryTimeout time.Duration, window int, slo float64) *CircuitBreaker {
    if failureThreshold <= 0 {
        failureThreshold = 1
    }
    if window <= 0 {
        window = 10
    }
    return &CircuitBreaker{
        state:               Closed,
        failureThreshold:    failureThreshold,
        baseFailureThreshold: failureThreshold,
        recoveryTimeout:     recoveryTimeout,
        baseRecoveryTimeout: recoveryTimeout,
        window:              window,
        slo:                 slo,
        name:                name,
    }
}

// Allows reports whether a request should be attempted.
func (cb *CircuitBreaker) Allows() bool {
    cb.mu.Lock()
    defer cb.mu.Unlock()

    switch cb.state {
    case Open:
        if time.Since(cb.openedAt) >= cb.recoveryTimeout {
            cb.state = HalfOpen
            breakerState.WithLabelValues(cb.name, "half_open").Inc()
            return true
        }
        return false
    default:
        return true
    }
}

func (cb *CircuitBreaker) recordSuccess() {
    cb.successes++
    cb.failures = 0
    if cb.state != Closed {
        cb.state = Closed
        cb.openedAt = time.Time{}
        breakerState.WithLabelValues(cb.name, "closed").Inc()
    }
    cb.adjust()
}

func (cb *CircuitBreaker) recordFailure() {
    cb.failures++
    if cb.failures >= cb.failureThreshold && cb.state != Open {
        cb.state = Open
        cb.openedAt = time.Now()
        breakerState.WithLabelValues(cb.name, "open").Inc()
    }
    cb.adjust()
}

// Execute runs op if allowed. When the circuit is open, fallback is invoked if not nil.
func (cb *CircuitBreaker) Execute(ctx context.Context, op func(context.Context) error, fallback func(context.Context) error) error {
    if !cb.Allows() {
        if fallback != nil {
            return fallback(ctx)
        }
        return ErrOpen
    }

    err := op(ctx)
    if err != nil {
        cb.recordFailure()
        if cb.state == Open && fallback != nil {
            return fallback(ctx)
        }
        return err
    }
    cb.recordSuccess()
    return nil
}

func (cb *CircuitBreaker) adjust() {
    total := cb.successes + cb.failures
    if total < cb.window {
        return
    }
    rate := float64(cb.successes) / float64(total)
    if rate < cb.slo {
        if cb.failureThreshold > 1 {
            cb.failureThreshold--
        }
        cb.recoveryTimeout *= 2
    } else {
        if cb.failureThreshold < cb.baseFailureThreshold {
            cb.failureThreshold++
        }
        if cb.recoveryTimeout > cb.baseRecoveryTimeout {
            cb.recoveryTimeout /= 2
            if cb.recoveryTimeout < cb.baseRecoveryTimeout {
                cb.recoveryTimeout = cb.baseRecoveryTimeout
            }
        }
    }
    cb.successes = 0
    cb.failures = 0
}

