package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/WSG23/yosai-gateway/events"
	"github.com/WSG23/yosai-gateway/internal/gateway"
)

func main() {
	brokers := os.Getenv("KAFKA_BROKERS")
	if brokers == "" {
		brokers = "localhost:9092"
	}
	processor, err := events.NewEventProcessor(brokers)
	if err != nil {
		log.Fatalf("failed to init event processor: %v", err)
	}
	defer processor.Close()

	g, err := gateway.New()
	if err != nil {
		log.Fatalf("failed to create gateway: %v", err)
	}

	// enable middleware based on env vars
	if os.Getenv("ENABLE_AUTH") == "1" {
		g.UseAuth()
	}
	if os.Getenv("ENABLE_RATELIMIT") == "1" {
		g.UseRateLimit()
	}

	addr := ":8080"
	if port := os.Getenv("PORT"); port != "" {
		addr = ":" + port
	}

	srv := &http.Server{Addr: addr, Handler: g.Handler()}

	go func() {
		log.Printf("starting gateway on %s", addr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("server error: %v", err)
		}
	}()

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
	<-stop

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil {
		log.Printf("shutdown error: %v", err)
	}
}
