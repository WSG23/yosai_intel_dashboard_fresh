package health

import (
	"bytes"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHandlers(t *testing.T) {
	h := NewManager()
	h.SetLive(true)
	h.SetReady(true)
	h.SetStartupComplete(true)

	rr := httptest.NewRecorder()
	h.Handler(rr, nil)
	if rr.Code != http.StatusOK {
		t.Fatalf("health status %d", rr.Code)
	}

	tests := []struct {
		handler http.HandlerFunc
		expect  string
	}{
		{h.LiveHandler, `{"status":"ok"}`},
		{h.ReadyHandler, `{"status":"ready"}`},
		{h.StartupHandler, `{"status":"complete"}`},
	}
	for _, tt := range tests {
		rr := httptest.NewRecorder()
		tt.handler(rr, nil)
		body, _ := io.ReadAll(rr.Body)
		if rr.Code != http.StatusOK {
			t.Fatalf("status %d", rr.Code)
		}
		if string(bytes.TrimSpace(body)) != tt.expect {
			t.Fatalf("unexpected body %s", string(body))
		}
	}
}
