package unit

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/require"

	gw "github.com/WSG23/yosai-gateway/internal/gateway"
)

func TestGatewayRBACHeaders(t *testing.T) {
	g, err := gw.New()
	require.NoError(t, err)

	paths := []string{
		"/api/v1/doors/foo",
		"/api/v1/analytics/foo",
		"/api/v1/events/foo",
		"/admin/foo",
	}

	for _, p := range paths {
		req := httptest.NewRequest(http.MethodGet, p, nil)
		resp := httptest.NewRecorder()
		g.Handler().ServeHTTP(resp, req)
		if resp.Code != http.StatusForbidden {
			t.Errorf("%s expected 403 got %d", p, resp.Code)
		}
	}
}
