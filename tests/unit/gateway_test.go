package unit

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/stretchr/testify/suite"

	gw "github.com/WSG23/yosai-gateway/internal/gateway"
)

type GatewaySuite struct {
	suite.Suite
	g *gw.Gateway
}

func (s *GatewaySuite) SetupTest() {
	var err error
	s.g, err = gw.New()
	s.Require().NoError(err)
}

func (s *GatewaySuite) TestHealthRoute() {
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	resp := httptest.NewRecorder()

	s.g.Handler().ServeHTTP(resp, req)

	s.Equal(http.StatusOK, resp.Code)
	s.Equal("ok", strings.TrimSpace(resp.Body.String()))
}

func (s *GatewaySuite) TestBreakerRoute() {
	req := httptest.NewRequest(http.MethodGet, "/breaker", nil)
	resp := httptest.NewRecorder()

	s.g.Handler().ServeHTTP(resp, req)

	s.Equal(http.StatusOK, resp.Code)
}

func TestGatewaySuite(t *testing.T) {
	suite.Run(t, new(GatewaySuite))
}
