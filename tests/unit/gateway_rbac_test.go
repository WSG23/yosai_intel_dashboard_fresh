package unit

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/require"

	gw "github.com/WSG23/yosai-gateway/internal/gateway"
)

func TestGatewayRBACHeadersDenied(t *testing.T) {
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

func TestGatewayRBACRoleAccess(t *testing.T) {
	g, err := gw.New()
	require.NoError(t, err)

	cases := []struct {
		path    string
		role    string
		allowed bool
	}{
		{"/api/v1/doors/foo", "admin", true},
		{"/api/v1/doors/foo", "analyst", false},
		{"/api/v1/analytics/foo", "analyst", true},
		{"/api/v1/analytics/foo", "viewer", true},
		{"/api/v1/events/foo", "admin", true},
		{"/api/v1/events/foo", "analyst", false},
		{"/admin/foo", "admin", true},
		{"/admin/foo", "viewer", false},
	}

	for _, c := range cases {
		req := httptest.NewRequest(http.MethodGet, c.path, nil)
		if c.role != "" {
			req.Header.Set("X-Roles", c.role)
		}
		resp := httptest.NewRecorder()
		g.Handler().ServeHTTP(resp, req)
		if c.allowed {
			if resp.Code == http.StatusForbidden {
				t.Errorf("%s with role %s expected allowed got %d", c.path, c.role, resp.Code)
			}
		} else {
			if resp.Code != http.StatusForbidden {
				t.Errorf("%s with role %s expected 403 got %d", c.path, c.role, resp.Code)
			}
		}
	}
}
