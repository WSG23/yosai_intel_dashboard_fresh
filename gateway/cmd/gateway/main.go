package main

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	_ "github.com/lib/pq"

	"github.com/WSG23/yosai-gateway/events"
	"github.com/WSG23/yosai-gateway/internal/cache"
	"github.com/WSG23/yosai-gateway/internal/engine"
	"github.com/WSG23/yosai-gateway/internal/gateway"
	"github.com/WSG23/yosai-gateway/internal/registry"
)

func main() {
	reg, err := registry.NewConsulRegistry(os.Getenv("CONSUL_ADDR"))
	if err != nil {
		log.Fatalf("failed to create registry: %v", err)
	}

	brokers, err := reg.ResolveService(context.Background(), "event-processor")
	if err != nil || brokers == "" {
		brokers = os.Getenv("KAFKA_BROKERS")
		if brokers == "" {
			brokers = "localhost:9092"
		}
	}
	cacheSvc := cache.NewRedisCache()

	dsn := fmt.Sprintf("host=%s port=%s user=%s dbname=%s password=%s sslmode=disable",
		os.Getenv("DB_HOST"), os.Getenv("DB_PORT"), os.Getenv("DB_USER"), os.Getenv("DB_NAME"), os.Getenv("DB_PASSWORD"))
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		log.Fatalf("failed to connect db: %v", err)
	}
	engCore, err := engine.NewRuleEngine(db)
	if err != nil {
		log.Fatalf("failed to init rule engine: %v", err)
	}
	ruleEngine := &engine.CachedRuleEngine{Engine: engCore, Cache: cacheSvc}

	processor, err := events.NewEventProcessor(brokers, cacheSvc, ruleEngine)
	if err != nil {
		log.Fatalf("failed to init event processor: %v", err)
	}
	defer processor.Close()

	analyticsAddr, err := reg.ResolveService(context.Background(), "analytics")
	if err == nil && analyticsAddr != "" {
		if host, port, err2 := net.SplitHostPort(analyticsAddr); err2 == nil {
			os.Setenv("APP_HOST", host)
			os.Setenv("APP_PORT", port)
		}
	}

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
