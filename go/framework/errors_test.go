package framework

import (
        "encoding/json"
        "net/http"
        "net/http/httptest"
        "strings"
        "testing"

        sharederrors "github.com/WSG23/errors"
)

func TestErrorHandler(t *testing.T) {
	h := NewErrorHandler()
	rr := httptest.NewRecorder()
	err := ServiceError{Code: sharederrors.Unauthorized, Message: "unauthorized"}

	h.Handle(rr, err)

	if rr.Code != http.StatusUnauthorized {
		t.Fatalf("expected %d got %d", http.StatusUnauthorized, rr.Code)
	}
        var m map[string]interface{}
        if err := json.NewDecoder(strings.NewReader(rr.Body.String())).Decode(&m); err != nil {
                t.Fatalf("decode: %v", err)
        }
        if m["code"] != string(sharederrors.Unauthorized) || m["message"] != "unauthorized" {
                t.Fatalf("unexpected body: %+v", m)
        }
        if _, ok := m["details"]; !ok {
                t.Fatalf("missing details field")
        }
}
