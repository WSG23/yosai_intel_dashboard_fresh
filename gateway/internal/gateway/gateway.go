package gateway

import (
	"net/http"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus/promhttp"

	"github.com/WSG23/yosai-gateway/internal/handlers"
	"github.com/WSG23/yosai-gateway/internal/proxy"
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
	r.PathPrefix("/").Handler(p)

	g := &Gateway{router: r, plugins: plugins.PluginRegistry{}}

	return g, nil
}

// Handler returns the root HTTP handler.
func (g *Gateway) Handler() http.Handler {
	return g.plugins.BuildMiddlewareChain(g.router)
}

// RegisterPlugin registers a gateway plugin.
func (g *Gateway) RegisterPlugin(p plugins.Plugin) {
	g.plugins.Register(p)
}
