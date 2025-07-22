package contract

import (
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	gw "github.com/WSG23/yosai-gateway/internal/gateway"
)

// TestHealthContract validates the contract for the /health endpoint.
func TestHealthContract(t *testing.T) {
	g, err := gw.New()
	require.NoError(t, err)

	server := httptest.NewServer(g.Handler())
	defer server.Close()

	resp, err := http.Get(server.URL + "/health")
	require.NoError(t, err)
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)

	assert.Equal(t, http.StatusOK, resp.StatusCode)
	assert.Equal(t, "ok", strings.TrimSpace(string(body)))
}
