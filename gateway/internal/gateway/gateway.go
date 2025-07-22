package gateway

import (
	"net/http"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus/promhttp"

	"github.com/WSG23/yosai-gateway/internal/handlers"
	imw "github.com/WSG23/yosai-gateway/internal/middleware"
	"github.com/WSG23/yosai-gateway/internal/proxy"
	"github.com/WSG23/yosai-gateway/internal/rbac"
	"github.com/WSG23/yosai-gateway/middleware"
	"github.com/WSG23/yosai-gateway/plugins"
)

// Gateway represents the HTTP gateway service.
type Gateway struct {
	router  *mux.Router
	plugins plugins.PluginRegistry
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
	doors.Use(imw.RequirePermissionHeader("doors.control"))
	doors.PathPrefix("/").Handler(p)

	analytics := r.PathPrefix("/api/v1/analytics").Subrouter()
	analytics.Use(imw.RequirePermissionHeader("analytics.read"))
	analytics.PathPrefix("/").Handler(p)

	events := r.PathPrefix("/api/v1/events").Subrouter()
	events.Use(imw.RequirePermissionHeader("events.write"))
	events.PathPrefix("/").Handler(p)

	admin := r.PathPrefix("/admin").Subrouter()
	admin.Use(imw.RequireRoleHeader("admin"))
	admin.PathPrefix("/").Handler(p)

	r.PathPrefix("/").Handler(p)

	g := &Gateway{router: r, plugins: plugins.PluginRegistry{}}

	return g, nil
}

// UseAuth enables auth middleware.
func (g *Gateway) UseAuth() {
	g.router.Use(imw.Auth)
}

// UseRateLimit enables rate limiting middleware.
func (g *Gateway) UseRateLimit(rl *middleware.RateLimiter) {
	g.router.Use(rl.Middleware)
}

// UseRBAC enables RBAC permission checks for all requests using the provided service and permission string.
func (g *Gateway) UseRBAC(s *rbac.RBACService, perm string) {
	g.router.Use(imw.RequirePermission(s, perm))
}

// Handler returns the root HTTP handler.
func (g *Gateway) Handler() http.Handler {
	return g.plugins.BuildMiddlewareChain(g.router)
}

// RegisterPlugin registers a gateway plugin.
func (g *Gateway) RegisterPlugin(p plugins.Plugin) {
	g.plugins.Register(p)
}
