package framework

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

        sharederrors "github.com/WSG23/errors"
)

type body struct {
	Code    string      `json:"code"`
	Message string      `json:"message"`
	Details interface{} `json:"details,omitempty"`
}

func TestErrorHandler(t *testing.T) {
	h := NewErrorHandler()
	rr := httptest.NewRecorder()
	err := ServiceError{Code: sharederrors.Unauthorized, Message: "unauthorized"}

	h.Handle(rr, err)

	if rr.Code != http.StatusUnauthorized {
		t.Fatalf("expected %d got %d", http.StatusUnauthorized, rr.Code)
	}
	var b body
	if err := json.NewDecoder(strings.NewReader(rr.Body.String())).Decode(&b); err != nil {
		t.Fatalf("decode: %v", err)
	}
	if b.Code != string(sharederrors.Unauthorized) || b.Message != "unauthorized" {
		t.Fatalf("unexpected body: %+v", b)
	}
}
