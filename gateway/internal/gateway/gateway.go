package gateway

import (
	"net/http"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus/promhttp"

	"github.com/WSG23/yosai-gateway/internal/handlers"
	"github.com/WSG23/yosai-gateway/internal/middleware"
	"github.com/WSG23/yosai-gateway/internal/proxy"
	"github.com/WSG23/yosai-gateway/internal/rbac"
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

// UseRBAC enables RBAC permission checks for all requests using the provided service and permission string.
func (g *Gateway) UseRBAC(s *rbac.RBACService, perm string) {
	g.router.Use(middleware.RequirePermission(s, perm))
}

// Handler returns the root HTTP handler.
func (g *Gateway) Handler() http.Handler {
	return g.router
}
