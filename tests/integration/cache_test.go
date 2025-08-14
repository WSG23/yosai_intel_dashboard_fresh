package integration

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"testing"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/redis/go-redis/v9"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	tc "github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/wait"

	gcache "github.com/WSG23/yosai-gateway/cache"
	"github.com/WSG23/yosai-gateway/internal/auth"
	icache "github.com/WSG23/yosai-gateway/internal/cache"
)

func TestCacheInvalidation(t *testing.T) {
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
	port, err := redisC.MappedPort(ctx, "6379")
	require.NoError(t, err)
	addr := fmt.Sprintf("%s:%s", host, port.Port())

	client := redis.NewClient(&redis.Options{Addr: addr})

	// Token cache test
	tcache := gcache.NewTokenCache(client)
	claims := &auth.EnhancedClaims{RegisteredClaims: jwt.RegisteredClaims{ID: "tok1"}}
	require.NoError(t, tcache.Set(ctx, "tok1", claims, time.Minute))
	c, err := tcache.Get(ctx, "tok1")
	require.NoError(t, err)
	require.NotNil(t, c)
	require.NoError(t, tcache.Delete(ctx, "tok1"))
	c, err = tcache.Get(ctx, "tok1")
	require.NoError(t, err)
	assert.Nil(t, c)

	// Decision cache test
	os.Setenv("REDIS_HOST", host)
	os.Setenv("REDIS_PORT", port.Port())
	dcache := icache.NewRedisCache()
	decision := icache.Decision{PersonID: "p1", DoorID: "d1", Decision: "allow"}
	require.NoError(t, dcache.SetDecision(ctx, decision))
	d, err := dcache.GetDecision(ctx, "p1", "d1")
	require.NoError(t, err)
	require.NotNil(t, d)
	require.NoError(t, dcache.InvalidateDecision(ctx, "p1", "d1"))
	d, err = dcache.GetDecision(ctx, "p1", "d1")
	require.NoError(t, err)
	assert.Nil(t, d)
}
