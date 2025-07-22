package gateway

import (
	"net/http"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus/promhttp"

	"github.com/WSG23/yosai-gateway/internal/handlers"
	"github.com/WSG23/yosai-gateway/internal/middleware"
	"github.com/WSG23/yosai-gateway/internal/proxy"
)

// Gateway represents the HTTP gateway service.
type Gateway struct {
	router *mux.Router
}

// New creates a configured Gateway.
func New() (*Gateway, error) {
	p, err := proxy.NewProxy()
	if err != nil {
		return nil, err
	}

	r := mux.NewRouter()
	r.HandleFunc("/health", handlers.HealthCheck).Methods(http.MethodGet)
	r.Handle("/metrics", promhttp.Handler()).Methods(http.MethodGet)
	r.HandleFunc("/breaker", handlers.BreakerMetrics).Methods(http.MethodGet)

	// Sensitive endpoint subrouters with access control
	doors := r.PathPrefix("/api/v1/doors").Subrouter()
	doors.Use(middleware.RequirePermission("doors.control"))
	doors.PathPrefix("/").Handler(p)

	analytics := r.PathPrefix("/api/v1/analytics").Subrouter()
	analytics.Use(middleware.RequirePermission("analytics.read"))
	analytics.PathPrefix("/").Handler(p)

	events := r.PathPrefix("/api/v1/events").Subrouter()
	events.Use(middleware.RequirePermission("events.write"))
	events.PathPrefix("/").Handler(p)

	admin := r.PathPrefix("/admin").Subrouter()
	admin.Use(middleware.RequireRole("admin"))
	admin.PathPrefix("/").Handler(p)

	r.PathPrefix("/").Handler(p)

	g := &Gateway{router: r}

	return g, nil
}

// UseAuth enables auth middleware.
func (g *Gateway) UseAuth() {
	g.router.Use(middleware.Auth)
}

// UseRateLimit enables rate limiting middleware.
func (g *Gateway) UseRateLimit() {
	g.router.Use(middleware.RateLimit)
}

// Handler returns the root HTTP handler.
func (g *Gateway) Handler() http.Handler {
	return g.router
}
