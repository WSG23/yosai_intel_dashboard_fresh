package main

import (
    "context"
    "log"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"

    "github.com/WSG23/yosai-gateway/internal/gateway"
    "github.com/WSG23/yosai-gateway/internal/middleware"
)

func main() {
    // Create gateway
    gw := gateway.New(gateway.Config{
        Port:            getEnv("GATEWAY_PORT", "8000"),
        ReadTimeout:     30 * time.Second,
        WriteTimeout:    30 * time.Second,
        ShutdownTimeout: 10 * time.Second,
    })

    // Setup routes
    gw.SetupRoutes()

    // Start server
    srv := &http.Server{
        Addr:         ":" + gw.Config.Port,
        Handler:      gw.Router,
        ReadTimeout:  gw.Config.ReadTimeout,
        WriteTimeout: gw.Config.WriteTimeout,
    }

    // Graceful shutdown
    go func() {
        sigint := make(chan os.Signal, 1)
        signal.Notify(sigint, os.Interrupt, syscall.SIGTERM)
        <-sigint

        ctx, cancel := context.WithTimeout(context.Background(), gw.Config.ShutdownTimeout)
        defer cancel()

        if err := srv.Shutdown(ctx); err != nil {
            log.Printf("Gateway shutdown error: %v", err)
        }
    }()

    log.Printf("Gateway starting on port %s", gw.Config.Port)
    if err := srv.ListenAndServe(); err != http.ErrServerClosed {
        log.Fatalf("Gateway error: %v", err)
    }
}

func getEnv(key, defaultValue string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return defaultValue
}
