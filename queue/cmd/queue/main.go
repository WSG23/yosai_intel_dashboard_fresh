package main

import (
    "log"
    "net/http"
    "os"

    "github.com/prometheus/client_golang/prometheus/promhttp"
)

func main() {
    addr := ":9091"
    if port := os.Getenv("PORT"); port != "" {
        addr = ":" + port
    }

    mux := http.NewServeMux()
    mux.Handle("/metrics", promhttp.Handler())
    mux.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) {
        w.WriteHeader(http.StatusOK)
        _, _ = w.Write([]byte("ok"))
    })

    log.Printf("starting queue metrics server on %s", addr)
    if err := http.ListenAndServe(addr, mux); err != nil {
        log.Fatalf("server error: %v", err)
    }
}
