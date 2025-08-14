package httpx

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
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

func TestDoJSON_CorrelationID(t *testing.T) {
	var got string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		got = r.Header.Get(CorrelationIDHeader)
		_ = json.NewEncoder(w).Encode(map[string]string{"ok": "true"})
	}))
	defer srv.Close()

	ctx, cid := WithCorrelationID(context.Background())
	req, err := http.NewRequest(http.MethodGet, srv.URL, nil)
	if err != nil {
		t.Fatalf("new request: %v", err)
	}
	var dst map[string]string
	if err := DoJSON(ctx, req, &dst); err != nil {
		t.Fatalf("do json: %v", err)
	}
	if got == "" || got != cid {
		t.Fatalf("expected correlation id %q, got %q", cid, got)
	}
}
