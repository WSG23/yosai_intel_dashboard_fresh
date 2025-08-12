package httpx

import (
	"strings"
	"testing"
)

type testStruct struct {
	A int `json:"a"`
}

func TestDecodeJSON(t *testing.T) {
	var dst testStruct
	if err := DecodeJSON(strings.NewReader(`{"a":1}`), &dst); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if dst.A != 1 {
		t.Fatalf("unexpected value: %v", dst.A)
	}
}

func TestDecodeJSONExtraTokens(t *testing.T) {
	var dst testStruct
	if err := DecodeJSON(strings.NewReader(`{"a":1}{"b":2}`), &dst); err == nil {
		t.Fatalf("expected error for extra tokens, got nil")
	}
}

func TestDecodeJSONWhitespace(t *testing.T) {
	var dst testStruct
	if err := DecodeJSON(strings.NewReader("{\"a\":1}\n"), &dst); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
}
