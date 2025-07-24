package framework

import (
	"io"
	"net/http"
	"os"
	"testing"
	"time"

	"go.uber.org/zap"

	"github.com/WSG23/yosai-framework/health"
	"github.com/WSG23/yosai-framework/logging"
	"github.com/WSG23/yosai-framework/metrics"
)

func writeConfig(t *testing.T, content string) string {
	t.Helper()
	dir := t.TempDir()
	path := dir + "/cfg.yaml"
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	return path
}

func TestServiceBuilder(t *testing.T) {
	b, err := NewServiceBuilder("test", "")
	if err != nil {
		t.Fatal(err)
	}
	hm := health.NewManager()
	b.WithHealth(hm)
	b.WithMetrics(metrics.NewPrometheusCollector("127.0.0.1:0", hm, &logging.ZapLogger{Logger: zap.NewNop()}))
	svc, err := b.Build()
	if err != nil {
		t.Fatal(err)
	}
	go svc.Start()
	defer svc.Stop()
	time.Sleep(100 * time.Millisecond)
	addr := svc.Metrics.ListenerAddr()
	resp, err := http.Get("http://" + addr + "/health")
	if err != nil {
		t.Fatal(err)
	}
	body, _ := io.ReadAll(resp.Body)
	resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("unexpected status %d", resp.StatusCode)
	}
	if string(body) != "{\"status\":\"ok\"}\n" && string(body) != "{\"status\":\"ok\"}" {
		t.Fatalf("unexpected body %s", string(body))
	}
}
