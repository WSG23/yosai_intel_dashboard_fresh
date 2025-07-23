package framework

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"go.uber.org/zap"
)

func writeConfig(t *testing.T, content string) string {
	t.Helper()
	dir := t.TempDir()
	path := filepath.Join(dir, "cfg.yaml")
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	return path
}

func TestSetupLoggingJSON(t *testing.T) {
	svc := &BaseService{Name: "test", Config: Config{LogLevel: "INFO"}}
	svc.ctx, svc.cancel = context.WithCancel(context.Background())
	r, w, _ := os.Pipe()
	orig := os.Stdout
	os.Stdout = w
	svc.setupLogging()
	svc.logger.Info("hello")
	w.Close()
	os.Stdout = orig
	data, _ := io.ReadAll(r)
	data = bytes.TrimSpace(data)
	if !bytes.HasPrefix(data, []byte("{")) {
		t.Fatalf("expected JSON log, got %s", string(data))
	}
	var m map[string]any
	if err := json.Unmarshal(data, &m); err != nil {
		t.Fatalf("invalid JSON log: %v", err)
	}
	if m["msg"] != "hello" {
		t.Fatalf("unexpected message %v", m["msg"])
	}
}

func TestMetricsInitialization(t *testing.T) {
	svc := &BaseService{Name: "test", Config: Config{MetricsAddr: "127.0.0.1:0"}}
	svc.ctx, svc.cancel = context.WithCancel(context.Background())
	svc.logger = zap.NewNop()
	svc.setupMetrics()
	svc.reqCount.WithLabelValues("GET", "/", "200").Inc()
	svc.reqDuration.WithLabelValues("GET", "/", "200").Observe(0.1)
	defer svc.Stop()
	addr := svc.metricsLn.Addr().String()
	resp, err := http.Get("http://" + addr + "/metrics")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if !strings.Contains(string(body), "yosai_request_total") {
		t.Fatalf("counter not exposed: %s", string(body))
	}
	if !strings.Contains(string(body), "yosai_request_duration_seconds") {
		t.Fatalf("histogram not exposed: %s", string(body))
	}
}

func TestHealthEndpoints(t *testing.T) {
	svc := &BaseService{Name: "test", Config: Config{MetricsAddr: "127.0.0.1:0"}}
	svc.ctx, svc.cancel = context.WithCancel(context.Background())
	svc.logger = zap.NewNop()
	svc.live = true
	svc.ready = true
	svc.startupComplete = true
	svc.setupMetrics()
	defer svc.Stop()

	addr := svc.metricsLn.Addr().String()
	tests := map[string]string{
		"/health":         `{"status":"ok"}`,
		"/health/live":    `{"status":"ok"}`,
		"/health/ready":   `{"status":"ready"}`,
		"/health/startup": `{"status":"complete"}`,
	}
	for path, exp := range tests {
		resp, err := http.Get("http://" + addr + path)
		if err != nil {
			t.Fatalf("request %s failed: %v", path, err)
		}
		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		if resp.StatusCode != http.StatusOK {
			t.Fatalf("%s returned %d", path, resp.StatusCode)
		}
		if strings.TrimSpace(string(body)) != exp {
			t.Fatalf("%s unexpected body %s", path, string(body))
		}
	}
}

func TestHealthNotReady(t *testing.T) {
	svc := &BaseService{Name: "test", Config: Config{MetricsAddr: "127.0.0.1:0"}}
	svc.ctx, svc.cancel = context.WithCancel(context.Background())
	svc.logger = zap.NewNop()
	svc.live = true
	svc.ready = false
	svc.startupComplete = true
	svc.setupMetrics()
	defer svc.Stop()

	addr := svc.metricsLn.Addr().String()
	resp, err := http.Get("http://" + addr + "/health/ready")
	if err != nil {
		t.Fatal(err)
	}
	body, _ := io.ReadAll(resp.Body)
	resp.Body.Close()
	if resp.StatusCode != http.StatusServiceUnavailable {
		t.Fatalf("expected 503, got %d", resp.StatusCode)
	}
	if strings.TrimSpace(string(body)) != `{"status":"not ready"}` {
		t.Fatalf("unexpected body %s", string(body))
	}
}

func TestHealthStartupIncomplete(t *testing.T) {
	svc := &BaseService{Name: "test", Config: Config{MetricsAddr: "127.0.0.1:0"}}
	svc.ctx, svc.cancel = context.WithCancel(context.Background())
	svc.logger = zap.NewNop()
	svc.live = true
	svc.ready = true
	svc.startupComplete = false
	svc.setupMetrics()
	defer svc.Stop()

	addr := svc.metricsLn.Addr().String()
	resp, err := http.Get("http://" + addr + "/health/startup")
	if err != nil {
		t.Fatal(err)
	}
	body, _ := io.ReadAll(resp.Body)
	resp.Body.Close()
	if resp.StatusCode != http.StatusServiceUnavailable {
		t.Fatalf("expected 503, got %d", resp.StatusCode)
	}
	if strings.TrimSpace(string(body)) != `{"status":"starting"}` {
		t.Fatalf("unexpected body %s", string(body))
	}
}
