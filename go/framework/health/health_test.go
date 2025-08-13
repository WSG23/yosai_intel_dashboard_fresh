package health

import (
	"bytes"
	"errors"
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
		body, err := io.ReadAll(rr.Body)
		if err != nil {
			t.Fatal(err)
		}
		if rr.Code != http.StatusOK {
			t.Fatalf("status %d", rr.Code)
		}
		if string(bytes.TrimSpace(body)) != tt.expect {
			t.Fatalf("unexpected body %s", string(body))
		}
	}
}

type errorWriter struct {
	http.ResponseWriter
	fail bool
}

func (e *errorWriter) Write(p []byte) (int, error) {
	if e.fail {
		e.fail = false
		return 0, errors.New("write error")
	}
	return e.ResponseWriter.Write(p)
}

func TestWriteJSONError(t *testing.T) {
	rr := httptest.NewRecorder()
	ew := &errorWriter{ResponseWriter: rr, fail: true}

	writeJSON(ew, "ok")

	if rr.Code != http.StatusInternalServerError {
		t.Fatalf("expected %d got %d", http.StatusInternalServerError, rr.Code)
	}
}
