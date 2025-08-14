package httpx

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestDefaultClientTimeout(t *testing.T) {
	if hc, ok := Default.httpClient.(*http.Client); !ok || hc.Timeout == 0 {
		t.Fatalf("expected non-zero client timeout")
	}
}

func TestDoJSON_Success(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_ = json.NewEncoder(w).Encode(map[string]string{"ok": "true"})
	}))
	defer srv.Close()

	req, err := http.NewRequest(http.MethodGet, srv.URL, nil)
	if err != nil {
		t.Fatalf("new request: %v", err)
	}
	var dst map[string]string
	if err := DoJSON(context.Background(), req, &dst); err != nil {
		t.Fatalf("do json: %v", err)
	}
	if dst["ok"] != "true" {
		t.Fatalf("unexpected response: %#v", dst)
	}
}

func TestDoJSON_ContextCancel(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		<-r.Context().Done()
	}))
	defer srv.Close()

	req, err := http.NewRequest(http.MethodGet, srv.URL, nil)
	if err != nil {
		t.Fatalf("new request: %v", err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Millisecond)
	defer cancel()
	var dst map[string]any
	if err := DoJSON(ctx, req, &dst); err == nil {
		t.Fatal("expected error for context cancellation")
	}
}

func TestNewTLSClient_Success(t *testing.T) {
	certDir := filepath.Join("..", "..", "deploy", "k8s", "certs")
	srvCert, err := tls.LoadX509KeyPair(filepath.Join(certDir, "gateway.crt"), filepath.Join(certDir, "gateway.key"))
	if err != nil {
		t.Fatalf("load server cert: %v", err)
	}
	caBytes, err := os.ReadFile(filepath.Join(certDir, "ca.crt"))
	if err != nil {
		t.Fatalf("read ca: %v", err)
	}
	pool := x509.NewCertPool()
	pool.AppendCertsFromPEM(caBytes)
	srv := httptest.NewUnstartedServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_ = json.NewEncoder(w).Encode(map[string]string{"ok": "true"})
	}))
	srv.TLS = &tls.Config{Certificates: []tls.Certificate{srvCert}, ClientAuth: tls.RequireAndVerifyClientCert, ClientCAs: pool}
	srv.StartTLS()
	defer srv.Close()

	client, err := NewTLSClient(filepath.Join(certDir, "httpx.crt"), filepath.Join(certDir, "httpx.key"), filepath.Join(certDir, "ca.crt"))
	if err != nil {
		t.Fatalf("new tls client: %v", err)
	}
	if hc, ok := client.httpClient.(*http.Client); ok {
		if tr, ok := hc.Transport.(*http.Transport); ok && tr.TLSClientConfig != nil {
			tr.TLSClientConfig.ServerName = "gateway"
		}
	}
	req, _ := http.NewRequest(http.MethodGet, srv.URL, nil)
	var dst map[string]string
	if err := client.DoJSON(context.Background(), req, &dst); err != nil {
		t.Fatalf("do json: %v", err)
	}
	if dst["ok"] != "true" {
		t.Fatalf("unexpected response: %#v", dst)
	}
}
