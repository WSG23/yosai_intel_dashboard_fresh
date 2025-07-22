package main

import (
	"fmt"
	"log"
	"net/http"

	"net/http/httputil"
	"net/url"
	"os"

	"github.com/gorilla/mux"
	"github.com/rs/cors"
)

// Config holds configuration for the gateway
type Config struct {
	ListenAddr string
	AppHost    string
	AppPort    string
}

// LoadConfig loads configuration from environment variables with defaults.
func LoadConfig() Config {
	return Config{
		ListenAddr: envOr("GATEWAY_ADDR", ":8080"),
		AppHost:    envOr("APP_HOST", "app"),
		AppPort:    envOr("APP_PORT", "8050"),
	}
}

func envOr(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}

// reverseProxy returns a reverse proxy handler to the dashboard service
func reverseProxy(cfg Config) (http.Handler, error) {
	target, err := url.Parse(fmt.Sprintf("http://%s:%s", cfg.AppHost, cfg.AppPort))
	if err != nil {
		return nil, err
	}
	return httputil.NewSingleHostReverseProxy(target), nil
}

func handleEvents(w http.ResponseWriter, r *http.Request) {
	// TODO: implement websocket/event forwarding
	w.WriteHeader(http.StatusNotImplemented)
}

func main() {
	cfg := LoadConfig()

	proxy, err := reverseProxy(cfg)
	if err != nil {
		log.Fatalf("failed to create proxy: %v", err)
	}

	r := mux.NewRouter()
	r.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	}).Methods(http.MethodGet)
	r.PathPrefix("/events").HandlerFunc(handleEvents)
	r.PathPrefix("/").Handler(proxy)

	handler := cors.AllowAll().Handler(r)

	log.Printf("gateway listening on %s", cfg.ListenAddr)
	if err := http.ListenAndServe(cfg.ListenAddr, handler); err != nil {
		log.Fatalf("server error: %v", err)
	}
}
