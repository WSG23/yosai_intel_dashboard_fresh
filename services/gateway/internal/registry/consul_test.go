package registry

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func newTestRegistry(t *testing.T, handler http.HandlerFunc) (*ConsulRegistry, *httptest.Server) {
	srv := httptest.NewServer(http.HandlerFunc(handler))
	t.Cleanup(srv.Close)
	cr, err := NewConsulRegistry(srv.Listener.Addr().String())
	if err != nil {
		t.Fatalf("new consul registry: %v", err)
	}
	return cr, srv
}

func TestRegisterService(t *testing.T) {
	called := false
	cr, _ := newTestRegistry(t, func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/agent/service/register" {
			http.NotFound(w, r)
			return
		}
		called = true
		if r.Method != http.MethodPut {
			t.Errorf("expected PUT, got %s", r.Method)
		}
		var body struct {
			Name    string
			Address string
			Port    int
		}
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			t.Fatalf("decode body: %v", err)
		}
		if body.Name != "svc" || body.Address != "1.2.3.4" || body.Port != 8080 {
			t.Errorf("unexpected body: %+v", body)
		}
		w.WriteHeader(http.StatusOK)
	})

	if err := cr.RegisterService(context.Background(), "svc", "1.2.3.4:8080"); err != nil {
		t.Fatalf("register service: %v", err)
	}
	if !called {
		t.Fatal("register endpoint not called")
	}
}

func TestResolveService(t *testing.T) {
	cr, _ := newTestRegistry(t, func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/health/service/svc" {
			http.NotFound(w, r)
			return
		}
		if r.URL.Query().Get("passing") != "1" {
			t.Errorf("expected passing=1, got %s", r.URL.RawQuery)
		}
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`[{"Service":{"Address":"1.2.3.4","Port":8080}}]`))
	})

	addr, err := cr.ResolveService(context.Background(), "svc")
	if err != nil {
		t.Fatalf("resolve service: %v", err)
	}
	if addr != "1.2.3.4:8080" {
		t.Fatalf("unexpected address %s", addr)
	}
}

func TestDeregisterService(t *testing.T) {
	called := false
	cr, _ := newTestRegistry(t, func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/agent/service/deregister/svc" {
			http.NotFound(w, r)
			return
		}
		called = true
		if r.Method != http.MethodPut {
			t.Errorf("expected PUT, got %s", r.Method)
		}
		w.WriteHeader(http.StatusOK)
	})

	if err := cr.DeregisterService(context.Background(), "svc"); err != nil {
		t.Fatalf("deregister service: %v", err)
	}
	if !called {
		t.Fatal("deregister endpoint not called")
	}
}
