package main

import (
	"context"
	"database/sql"
	"fmt"

	"net"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	_ "github.com/lib/pq"

	"github.com/WSG23/yosai-gateway/events"
	"github.com/WSG23/yosai-gateway/internal/cache"
	cfg "github.com/WSG23/yosai-gateway/internal/config"
	"github.com/WSG23/yosai-gateway/internal/engine"
	"github.com/WSG23/yosai-gateway/internal/gateway"
	"github.com/WSG23/yosai-gateway/internal/rbac"
	reg "github.com/WSG23/yosai-gateway/internal/registry"
	"github.com/WSG23/yosai-gateway/internal/tracing"
	"github.com/WSG23/yosai-gateway/plugins"
	"github.com/sony/gobreaker"
)

func main() {
	shutdown, err := tracing.InitTracing("gateway")
	if err != nil {
		tracing.Logger.Fatalf("failed to init tracing: %v", err)
	}
	defer shutdown(context.Background())

	brokers := os.Getenv("KAFKA_BROKERS")
	if brokers == "" {
		brokers = "localhost:9092"

	}
	cacheSvc := cache.NewRedisCache()
	rbacSvc := rbac.New(time.Minute)

	cbConf, err := cfg.Load(os.Getenv("CIRCUIT_BREAKER_CONFIG"))
	if err != nil {
		tracing.Logger.WithError(err).Warn("failed to load circuit breaker config, using defaults")
		cbConf = &cfg.Config{}
	}

	dbName := os.Getenv("DB_GATEWAY_NAME")
	if dbName == "" {
		dbName = os.Getenv("DB_NAME")
	}
	dsn := fmt.Sprintf("host=%s port=%s user=%s dbname=%s password=%s sslmode=disable",
		os.Getenv("DB_HOST"), os.Getenv("DB_PORT"), os.Getenv("DB_USER"), dbName, os.Getenv("DB_PASSWORD"))
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		tracing.Logger.Fatalf("failed to connect db: %v", err)
	}
	dbSettings := gobreaker.Settings{
		Name:    "rule-engine",
		Timeout: cbConf.Database.Timeout(),
		ReadyToTrip: func(c gobreaker.Counts) bool {
			t := cbConf.Database.FailureThreshold
			if t <= 0 {
				t = 5
			}
			return c.ConsecutiveFailures >= uint32(t)
		},
	}
	engCore, err := engine.NewRuleEngineWithSettings(db, dbSettings)
	if err != nil {
		tracing.Logger.Fatalf("failed to init rule engine: %v", err)
	}
	ruleEngine := &engine.CachedRuleEngine{Engine: engCore, Cache: cacheSvc}

	epSettings := gobreaker.Settings{
		Name:    "event-processor",
		Timeout: cbConf.EventProcessor.Timeout(),
		ReadyToTrip: func(c gobreaker.Counts) bool {
			t := cbConf.EventProcessor.FailureThreshold
			if t <= 0 {
				t = 10
			}
			return c.ConsecutiveFailures >= uint32(t)
		},
	}
	processor, err := events.NewEventProcessor(brokers, cacheSvc, ruleEngine, epSettings)
	if err != nil {
		tracing.Logger.Fatalf("failed to init event processor: %v", err)
	}
	defer processor.Close()

	registryAddr := os.Getenv("SERVICE_REGISTRY_URL")
	r, err := reg.NewConsulRegistry(registryAddr)
	if err == nil {
		if analyticsAddr, err := r.ResolveService(context.Background(), "analytics"); err == nil && analyticsAddr != "" {
			if host, port, err2 := net.SplitHostPort(analyticsAddr); err2 == nil {
				os.Setenv("APP_HOST", host)
				os.Setenv("APP_PORT", port)
			}
		}
	}

	g, err := gateway.New()
	if err != nil {
		tracing.Logger.Fatalf("failed to create gateway: %v", err)
	}

	// load plugins from configuration
	loaded, err := plugins.LoadPlugins("")
	if err != nil {
		tracing.Logger.WithError(err).Warn("failed to load gateway plugins")
	}
	if os.Getenv("ENABLE_RBAC") == "1" {
		g.UseRBAC(rbacSvc, "gateway.access")
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
		tracing.Logger.Infof("starting gateway on %s", addr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			tracing.Logger.Fatalf("server error: %v", err)
		}
	}()

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
	<-stop

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil {
		tracing.Logger.Errorf("shutdown error: %v", err)
	}
}
