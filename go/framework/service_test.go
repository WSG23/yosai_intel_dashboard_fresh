package framework

import (
	"io"
	"net/http"
	"net/http/httptest"
	"testing"

	"go.uber.org/zap"

	"github.com/WSG23/yosai-framework/health"
	"github.com/WSG23/yosai-framework/logging"
	"github.com/WSG23/yosai-framework/metrics"
)

func TestServiceBuilder(t *testing.T) {
	b, err := NewServiceBuilder("test", "")
	if err != nil {
		t.Fatal(err)
	}
	hm := health.NewManager()
	b.WithHealth(hm)
	b.WithMetrics(metrics.NewPrometheusCollector("", hm, &logging.ZapLogger{Logger: zap.NewNop()}))
	svc, err := b.Build()
	if err != nil {
		t.Fatal(err)
	}
	svc.Health.SetStartupComplete(true)
	svc.Health.SetReady(true)
	svc.Health.SetLive(true)
	rr := httptest.NewRecorder()
	svc.Health.Handler(rr, httptest.NewRequest(http.MethodGet, "/health", nil))
	if rr.Code != http.StatusOK {
		t.Fatalf("unexpected status %d", rr.Code)
	}
	body, err := io.ReadAll(rr.Body)
	if err != nil {
		t.Fatal(err)
	}
	if string(body) != "{\"status\":\"ok\"}\n" && string(body) != "{\"status\":\"ok\"}" {
		t.Fatalf("unexpected body %s", string(body))
	}
}
