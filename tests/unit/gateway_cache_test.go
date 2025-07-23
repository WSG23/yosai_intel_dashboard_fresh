package unit

import (
	"context"
	"net"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os/exec"
	"testing"
	"time"

	"github.com/redis/go-redis/v9"
	"github.com/stretchr/testify/require"
	tc "github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/wait"

	gw "github.com/WSG23/yosai-gateway/internal/gateway"
	"github.com/WSG23/yosai-gateway/plugins/cache"
)

func TestGatewayCachePlugin(t *testing.T) {
	if _, err := exec.LookPath("docker"); err != nil {
		t.Skip("docker not available")
	}

	ctx := context.Background()
	redisC, err := tc.GenericContainer(ctx, tc.GenericContainerRequest{
		ContainerRequest: tc.ContainerRequest{
			Image:        "redis:7-alpine",
			ExposedPorts: []string{"6379/tcp"},
			WaitingFor:   wait.ForListeningPort("6379/tcp"),
		},
		Started: true,
	})
	require.NoError(t, err)
	defer redisC.Terminate(ctx)

	host, err := redisC.Host(ctx)
	require.NoError(t, err)
	port, err := redisC.MappedPort(ctx, "6379/tcp")
	require.NoError(t, err)

	client := redis.NewClient(&redis.Options{Addr: net.JoinHostPort(host, port.Port())})

	backendHits := 0
	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		backendHits++
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("ok"))
	}))
	defer backend.Close()

	u, _ := url.Parse(backend.URL)
	bHost, bPort, _ := net.SplitHostPort(u.Host)
	t.Setenv("APP_HOST", bHost)
	t.Setenv("APP_PORT", bPort)

	g, err := gw.New()
	require.NoError(t, err)
	g.RegisterPlugin(cache.NewCachePlugin(client, []cache.CacheRule{{Path: "/foo", TTL: time.Second}}))

	server := httptest.NewServer(g.Handler())
	defer server.Close()

	resp1, err := http.Get(server.URL + "/foo")
	require.NoError(t, err)
	require.Equal(t, "MISS", resp1.Header.Get("X-Cache"))

	resp2, err := http.Get(server.URL + "/foo")
	require.NoError(t, err)
	require.Equal(t, "HIT", resp2.Header.Get("X-Cache"))

	require.Equal(t, 1, backendHits)
}
