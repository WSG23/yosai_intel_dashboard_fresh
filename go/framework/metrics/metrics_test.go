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
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	if err := c.Start(ctx); err != nil {
		t.Fatal(err)
	}
	defer func() {
		if err := c.Stop(context.Background()); err != nil {
			t.Fatal(err)
		}
	}()
	c.Requests().WithLabelValues("GET", "/", "200").Inc()
	req, err := http.NewRequestWithContext(context.Background(), http.MethodGet, "http://"+c.ListenerAddr()+"/metrics", nil)
	if err != nil {
		t.Fatal(err)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		t.Fatal(err)
	}
	if err := resp.Body.Close(); err != nil {
		t.Fatal(err)
	}
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("unexpected status %d", resp.StatusCode)
	}
	if !strings.Contains(string(body), "yosai_request_total") {
		t.Fatalf("counter not exposed: %s", string(body))
	}
}
