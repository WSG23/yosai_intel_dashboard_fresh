package websocket

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestProxyPluginPassThrough(t *testing.T) {
	p := &ProxyPlugin{routes: []Route{{Path: "/ws", Backend: "ws://backend"}}}
	called := false
	next := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		called = true
	})

	req := httptest.NewRequest(http.MethodGet, "/ws", nil)
	rw := httptest.NewRecorder()
	p.Process(context.Background(), req, rw, next)

	if !called {
		t.Fatal("next handler not called for non-upgrade request")
	}
}

func TestIsWebSocketRequest(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/ws", nil)
	if isWebSocketRequest(req) {
		t.Fatal("unexpected websocket detection")
	}
	req.Header.Set("Connection", "Upgrade")
	req.Header.Set("Upgrade", "websocket")
	if !isWebSocketRequest(req) {
		t.Fatal("expected websocket upgrade")
	}
}
