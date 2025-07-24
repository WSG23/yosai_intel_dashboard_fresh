package metrics

import (
	"context"
	"io"
	"net/http"
	"strings"
	"testing"

	"go.uber.org/zap"

	"github.com/WSG23/yosai-framework/health"
	"github.com/WSG23/yosai-framework/logging"
)

func TestPrometheusCollector(t *testing.T) {
	hm := health.NewManager()
	logger := &logging.ZapLogger{Logger: zap.NewNop()}
	c := NewPrometheusCollector("127.0.0.1:0", hm, logger)
	if err := c.Start(); err != nil {
		t.Fatal(err)
	}
	defer c.Stop(context.Background())
	c.Requests().WithLabelValues("GET", "/", "200").Inc()
	resp, err := http.Get("http://" + c.ListenerAddr() + "/metrics")
	if err != nil {
		t.Fatal(err)
	}
	body, _ := io.ReadAll(resp.Body)
	resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("unexpected status %d", resp.StatusCode)
	}
	if !strings.Contains(string(body), "yosai_request_total") {
		t.Fatalf("counter not exposed: %s", string(body))
	}
}
