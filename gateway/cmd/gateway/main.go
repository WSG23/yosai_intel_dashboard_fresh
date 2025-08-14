package main

import (
	"context"
	"database/sql"
	"log"

	"crypto/tls"
	"crypto/x509"
	"net"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"syscall"
	"time"

	vault "github.com/hashicorp/vault/api"

	_ "github.com/lib/pq"

	"github.com/WSG23/yosai-gateway/events"
	"github.com/WSG23/yosai-gateway/internal/cache"
	cbcfg "github.com/WSG23/yosai-gateway/internal/config"
	gwconfig "github.com/WSG23/yosai-gateway/internal/config"
	"github.com/WSG23/yosai-gateway/internal/engine"
	"github.com/WSG23/yosai-gateway/internal/gateway"
	reg "github.com/WSG23/yosai-gateway/internal/registry"
	"github.com/WSG23/yosai-gateway/internal/tracing"
	mw "github.com/WSG23/yosai-gateway/middleware"
	apicache "github.com/WSG23/yosai-gateway/plugins/cache"
	"github.com/redis/go-redis/v9"

	framework "github.com/WSG23/yosai-framework"

	"github.com/sony/gobreaker"

	xerrors "github.com/WSG23/errors"
)

func validateRequiredEnv(vars []string) {
	missing := []string{}
	for _, v := range vars {
		if os.Getenv(v) == "" {
			missing = append(missing, v)
		}
	}
	if len(missing) > 0 {
		log.Fatalf("missing required environment variables: %s", strings.Join(missing, ", "))
	}
}

func newVaultClient() (*vault.Client, error) {
	cfg := vault.DefaultConfig()
	if err := cfg.ReadEnvironment(); err != nil {
		return nil, err
	}
	c, err := vault.NewClient(cfg)
	if err != nil {
		return nil, err
	}
	token := os.Getenv("VAULT_TOKEN")
	if token == "" {
		return nil, xerrors.Errorf("VAULT_TOKEN not set")
	}
	c.SetToken(token)
	return c, nil
}

func readVaultField(c *vault.Client, path string) (string, error) {
	parts := strings.SplitN(path, "#", 2)
	if len(parts) != 2 {
		return "", xerrors.Errorf("invalid vault path %q", path)
	}
	p, field := parts[0], parts[1]
	secretPath := strings.TrimPrefix(p, "secret/data/")
	s, err := c.KVv2("secret").Get(context.Background(), secretPath)
	if err != nil {
		return "", err
	}
	val, ok := s.Data[field].(string)
	if !ok {
		return "", xerrors.Errorf("field %s not found at %s", field, p)
	}
	return val, nil
}

func main() {
	b, err := framework.NewServiceBuilder("gateway", "")
	if err != nil {
		log.Fatalf("failed to init service builder: %v", err)
	}
	svc, err := b.Build()
	if err != nil {
		log.Fatalf("failed to build service: %v", err)
	}
	go svc.Start()
	defer svc.Stop()

	validateRequiredEnv([]string{"DB_HOST", "DB_PORT", "DB_USER", "DB_GATEWAY_NAME"})

	vclient, err := newVaultClient()
	if err != nil {
		log.Fatalf("failed to init vault client: %v", err)
	}
	dbPassword, err := readVaultField(vclient, "secret/data/db#password")
	if err != nil {
		log.Fatalf("failed to read db password: %v", err)
	}
	jwtSecret, err := readVaultField(vclient, "secret/data/jwt#secret")
	if err != nil {
		log.Fatalf("failed to read jwt secret: %v", err)
	}

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

	cbConf, err := cbcfg.Load(os.Getenv("CIRCUIT_BREAKER_CONFIG"))
	if err != nil {
		tracing.Logger.WithError(err).Warn("failed to load circuit breaker config, using defaults")
		cbConf = &cbcfg.Config{}
	}

	dbName := os.Getenv("DB_GATEWAY_NAME")
	if dbName == "" {
		dbName = os.Getenv("DB_NAME")
	}
	sslMode := os.Getenv("DB_SSLMODE")
	if sslMode == "" {
		sslMode = "require"
	}
	dsn := fmt.Sprintf("host=%s port=%s user=%s dbname=%s password=%s sslmode=%s",
		os.Getenv("DB_HOST"), os.Getenv("DB_PORT"), os.Getenv("DB_USER"), dbName, dbPassword, sslMode)
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
	cacheSize := 64
	if v := os.Getenv("RULE_ENGINE_STMT_CACHE_SIZE"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 {
			cacheSize = n
		}
	}
	engCore, err := engine.NewRuleEngineWithSettings(db, dbSettings, cacheSize)
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
		g.UseAuth([]byte(jwtSecret))

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
	srv := &http.Server{Addr: addr, Handler: g.Handler(), TLSConfig: tlsCfg}

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
