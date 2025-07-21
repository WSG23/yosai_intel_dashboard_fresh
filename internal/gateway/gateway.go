package gateway

import (
    "net/http"
    "time"

    "github.com/gorilla/mux"
    "github.com/WSG23/yosai-gateway/internal/handlers"
    "github.com/WSG23/yosai-gateway/internal/middleware"
    "github.com/WSG23/yosai-gateway/internal/proxy"
)

type Config struct {
    Port            string
    ReadTimeout     time.Duration
    WriteTimeout    time.Duration
    ShutdownTimeout time.Duration
}

type Gateway struct {
    Config  Config
    Router  *mux.Router
    proxies map[string]*proxy.ServiceProxy
}

func New(config Config) *Gateway {
    return &Gateway{
        Config:  config,
        Router:  mux.NewRouter(),
        proxies: make(map[string]*proxy.ServiceProxy),
    }
}

func (g *Gateway) SetupRoutes() {
    // Apply global middleware
    g.Router.Use(middleware.Logger)
    g.Router.Use(middleware.CORS)
    g.Router.Use(middleware.RateLimit)
    g.Router.Use(middleware.Authentication)

    // Health check
    g.Router.HandleFunc("/health", handlers.HealthCheck).Methods("GET")

    // Service routes
    g.setupServiceRoutes()

    // API documentation
    g.Router.PathPrefix("/api/docs").Handler(
        http.StripPrefix("/api/docs", http.FileServer(http.Dir("./docs"))),
    )
}

func (g *Gateway) setupServiceRoutes() {
    // Analytics service routes
    analytics := g.Router.PathPrefix("/api/v1/analytics").Subrouter()
    analytics.Use(middleware.RequireAuth)
    g.proxies["analytics"] = proxy.New("analytics-service:8001")
    analytics.HandleFunc("/{path:.*}", g.proxies["analytics"].Handle)

    // Event processing routes
    events := g.Router.PathPrefix("/api/v1/events").Subrouter()
    events.Use(middleware.RequireAuth)
    events.Use(middleware.ValidateEvent)
    g.proxies["events"] = proxy.New("event-service:8002")
    events.HandleFunc("/{path:.*}", g.proxies["events"].Handle)

    // Access control routes
    access := g.Router.PathPrefix("/api/v1/access").Subrouter()
    access.Use(middleware.RequireAuth)
    access.Use(middleware.AuditLog)
    g.proxies["access"] = proxy.New("access-service:8003")
    access.HandleFunc("/{path:.*}", g.proxies["access"].Handle)

    // Legacy Python service routes (during migration)
    legacy := g.Router.PathPrefix("/api/v1/legacy").Subrouter()
    g.proxies["legacy"] = proxy.New("python-api:8050")
    legacy.HandleFunc("/{path:.*}", g.proxies["legacy"].Handle)
}
