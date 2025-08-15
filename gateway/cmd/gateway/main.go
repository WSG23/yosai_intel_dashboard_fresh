package main

import (
	"context"
	"database/sql"
	"fmt"

	"crypto/tls"
	"crypto/x509"
	"net"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	ckafka "github.com/confluentinc/confluent-kafka-go/kafka"

	_ "github.com/lib/pq"

	"github.com/WSG23/yosai-gateway/internal/cache"
	cbcfg "github.com/WSG23/yosai-gateway/internal/config"
	gwconfig "github.com/WSG23/yosai-gateway/internal/config"
	rtconfig "github.com/WSG23/yosai-gateway/internal/config"
	"github.com/WSG23/yosai-gateway/internal/engine"
	"github.com/WSG23/yosai-gateway/internal/gateway"
	reg "github.com/WSG23/yosai-gateway/internal/registry"
	"github.com/WSG23/yosai-gateway/internal/tracing"
	mw "github.com/WSG23/yosai-gateway/middleware"
	apicache "github.com/WSG23/yosai-gateway/plugins/cache"
	"github.com/redis/go-redis/v9"

	framework "github.com/WSG23/yosai-framework"

	"github.com/sony/gobreaker"

	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
)

// @title           Yōsai Gateway API
// @version         1.0
// @description     API documentation for the Yōsai gateway service.
// @BasePath        /
func main() {
	b, err := framework.NewServiceBuilder("gateway", "")
	if err != nil {
		tracing.Logger.Fatalf("failed to init service builder: %v", err)
	}
	svc, err := b.Build()
	if err != nil {
		tracing.Logger.Fatalf("failed to build service: %v", err)
	}
	go svc.Start()
	defer svc.Stop()

	cfg, err := rtconfig.Load()
	if err != nil {
		tracing.Logger.Fatalf("failed to load runtime config: %v", err)
	}

	shutdown, err := tracing.InitTracing("gateway")
	if err != nil {
		tracing.Logger.Fatalf("failed to init tracing: %v", err)
	}
	defer shutdown(context.Background())

	brokers := cfg.KafkaBrokers
	cacheSvc := cache.NewRedisCache()

	cbConf, err := cbcfg.LoadCircuitBreakers(os.Getenv("CIRCUIT_BREAKER_CONFIG"))
	if err != nil {
		tracing.Logger.WithError(err).Warn("failed to load circuit breaker config, using defaults")
		cbConf = &cbcfg.Config{}
	}

	dsn := fmt.Sprintf("host=%s port=%s user=%s dbname=%s password=%s sslmode=%s",
		cfg.DBHost, cfg.DBPort, cfg.DBUser, cfg.DBName, cfg.DBPassword, cfg.DBSSLMode)
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		tracing.Logger.Fatalf("failed to connect db: %v", err)
	}
	if err := db.PingContext(context.Background()); err != nil {
		tracing.Logger.Fatalf("failed to ping db: %v", err)
	}
	producer, err := ckafka.NewProducer(&ckafka.ConfigMap{
		"bootstrap.servers":  brokers,
		"enable.idempotence": true,
		"acks":               "all",
		"transactional.id":   "gateway-outbox",
	})
	if err != nil {
		tracing.Logger.Fatalf("failed to init kafka producer: %v", err)
	}
	defer producer.Close()
	outbox := engine.NewOutbox(db)
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
	cacheSize := 64
	if v := os.Getenv("RULE_ENGINE_STMT_CACHE_SIZE"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 {
			cacheSize = n
		}
	}
	engCore, err := engine.NewRuleEngineWithSettings(db, outbox, dbSettings, cacheSize)
	if err != nil {
		tracing.Logger.Fatalf("failed to init rule engine: %v", err)
	}
	ruleEngine := &engine.CachedRuleEngine{Engine: engCore, Cache: cacheSvc}
	publisher := engine.NewOutboxPublisher(outbox, producer, time.Second)
	go publisher.Run(context.Background())

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
	g.UseRequestID()

	// Load plugin configuration and register plugins
	gwConf, err := gwconfig.LoadGateway(os.Getenv("GATEWAY_CONFIG"))
	if err != nil {
		tracing.Logger.Fatalf("failed to load gateway config: %v", err)
	}
	for _, pc := range gwConf.Gateway.Plugins {
		if !pc.Enabled {
			continue
		}
		switch pc.Name {
		case "cache":
			host := os.Getenv("REDIS_HOST")
			if host == "" {
				host = "localhost"
			}
			port := os.Getenv("REDIS_PORT")
			if port == "" {
				port = "6379"
			}
			client := redis.NewClient(&redis.Options{Addr: host + ":" + port})
			var rules []apicache.CacheRule
			for _, r := range pc.Config.Rules {
				rules = append(rules, apicache.CacheRule{
					Path:            r.Path,
					TTL:             r.TTL,
					VaryHeaders:     r.VaryHeaders,
					VaryParams:      r.VaryParams,
					InvalidatePaths: r.InvalidatePaths,
				})
			}
			g.RegisterPlugin(apicache.NewCachePlugin(client, rules))
		}
	}

	// enable middleware based on env vars
	if os.Getenv("ENABLE_AUTH") == "1" {
		g.UseAuth([]byte(cfg.JWTSecret))

	}

	rlConf, err := gwconfig.LoadRateLimit(os.Getenv("RATE_LIMIT_CONFIG"))
	if err != nil {
		tracing.Logger.WithError(err).Warn("failed to load rate limit config, using defaults")
		rlConf = &gwconfig.RateLimitSettings{}
	}
	if v := os.Getenv("RATE_LIMIT_BUCKET"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 {
			rlConf.Burst = n
		}
	}
	window := time.Minute
	if v := os.Getenv("RATE_LIMIT_INTERVAL_MS"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 {
			window = time.Duration(n) * time.Millisecond
		}
	}
	host := os.Getenv("REDIS_HOST")
	if host == "" {
		host = "localhost"
	}
	port := os.Getenv("REDIS_PORT")
	if port == "" {
		port = "6379"
	}
	rlClient := redis.NewClient(&redis.Options{Addr: host + ":" + port})
	limiter := mw.NewRateLimiter(rlClient, *rlConf)
	limiter.SetWindow(window)
	g.UseRateLimit(limiter)
	g.UseSecurityHeaders()

	addr := ":8080"
	if port := os.Getenv("PORT"); port != "" {
		addr = ":" + port
	}

	tlsCert := os.Getenv("TLS_CERT_FILE")
	tlsKey := os.Getenv("TLS_KEY_FILE")
	tlsCA := os.Getenv("TLS_CA_FILE")
	tlsCfg := &tls.Config{}
	if tlsCA != "" {
		caBytes, err := os.ReadFile(tlsCA)
		if err == nil {
			pool := x509.NewCertPool()
			if pool.AppendCertsFromPEM(caBytes) {
				tlsCfg.ClientCAs = pool
				tlsCfg.ClientAuth = tls.RequireAndVerifyClientCert
			}
		}
	}
	srv := &http.Server{Addr: addr, Handler: otelhttp.NewHandler(g.Handler(), "http"), TLSConfig: tlsCfg}

	go func() {
		tracing.Logger.Infof("starting gateway on %s", addr)
		var err error
		if tlsCert != "" && tlsKey != "" {
			err = srv.ListenAndServeTLS(tlsCert, tlsKey)
		} else {
			err = srv.ListenAndServe()
		}
		if err != nil && err != http.ErrServerClosed {
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
