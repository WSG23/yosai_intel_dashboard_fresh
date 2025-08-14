package main

import (
	"context"
	"log"
	"net/http"
	"os"

	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	"yourmodule/tracing"
)

func main() {
	addr := ":9091"
	if port := os.Getenv("PORT"); port != "" {
		addr = ":" + port
	}
	ctx := context.Background()
	shutdown, err := tracing.Init(ctx, "queue", nil)
	if err != nil {
		log.Fatalf("tracing init: %v", err)
	}
	defer shutdown(ctx)

	mux := http.NewServeMux()
	mux.Handle("/metrics", promhttp.Handler())
	mux.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	})

	log.Printf("starting queue metrics server on %s", addr)
	if err := http.ListenAndServe(addr, otelhttp.NewHandler(mux, "http")); err != nil {
		log.Fatalf("server error: %v", err)
	}
}
