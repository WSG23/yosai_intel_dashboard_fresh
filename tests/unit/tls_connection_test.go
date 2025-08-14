package unit

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

	httpx "github.com/WSG23/pkg/httpx"
)

func certPath(name string) string {
	return filepath.Join("..", "..", "deploy", "k8s", "certs", name)
}

func TestTLSConnection(t *testing.T) {
	cert, err := tls.LoadX509KeyPair(certPath("gateway.crt"), certPath("gateway.key"))
	if err != nil {
		t.Fatal(err)
	}
	caCert, err := os.ReadFile(certPath("ca.crt"))
	if err != nil {
		t.Fatal(err)
	}
	pool := x509.NewCertPool()
	pool.AppendCertsFromPEM(caCert)

	srv := httptest.NewUnstartedServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(map[string]bool{"ok": true})
	}))
	srv.TLS = &tls.Config{Certificates: []tls.Certificate{cert}, ClientAuth: tls.RequireAndVerifyClientCert, ClientCAs: pool}
	srv.StartTLS()
	defer srv.Close()

	client, err := httpx.NewTLSClient(certPath("httpx.crt"), certPath("httpx.key"), certPath("ca.crt"))
	if err != nil {
		t.Fatal(err)
	}
	req, _ := http.NewRequest("GET", srv.URL, nil)
	var dst map[string]bool
	if err := client.DoJSON(context.Background(), req, &dst); err != nil {
		t.Fatalf("request failed: %v", err)
	}
	if !dst["ok"] {
		t.Fatalf("unexpected response: %#v", dst)
	}
}

func TestTLSConnectionFailsWithoutClientCert(t *testing.T) {
	cert, err := tls.LoadX509KeyPair(certPath("gateway.crt"), certPath("gateway.key"))
	if err != nil {
		t.Fatal(err)
	}
	caCert, err := os.ReadFile(certPath("ca.crt"))
	if err != nil {
		t.Fatal(err)
	}
	pool := x509.NewCertPool()
	pool.AppendCertsFromPEM(caCert)
	srv := httptest.NewUnstartedServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	srv.TLS = &tls.Config{Certificates: []tls.Certificate{cert}, ClientAuth: tls.RequireAndVerifyClientCert, ClientCAs: pool}
	srv.StartTLS()
	defer srv.Close()

	tr := &http.Transport{TLSClientConfig: &tls.Config{RootCAs: pool}}
	c := &http.Client{Transport: tr}
	_, err = c.Get(srv.URL)
	if err == nil {
		t.Fatal("expected error without client cert")
	}
}
