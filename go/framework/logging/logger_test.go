package logging

import (
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"os"
	"syscall"
	"testing"
)

func TestZapLoggerJSON(t *testing.T) {
	r, w, err := os.Pipe()
	if err != nil {
		t.Fatal(err)
	}
	orig := os.Stdout
	os.Stdout = w
	lg, err := NewZapLogger("test", "INFO")
	if err != nil {
		t.Fatal(err)
	}
	lg.Info("hello")
	if err := lg.Sync(); err != nil && !errors.Is(err, syscall.ENOTTY) && !errors.Is(err, syscall.EINVAL) {

		t.Fatal(err)
	}
	if err := w.Close(); err != nil {
		t.Fatal(err)
	}
	os.Stdout = orig
	data, err := io.ReadAll(r)
	if err != nil {
		t.Fatal(err)
	}
	data = bytes.TrimSpace(data)
	if !bytes.HasPrefix(data, []byte("{")) {
		t.Fatalf("expected JSON log, got %s", string(data))
	}
	var m map[string]any
	if err := json.Unmarshal(data, &m); err != nil {
		t.Fatalf("invalid JSON log: %v", err)
	}
	if m["msg"] != "hello" {
		t.Fatalf("unexpected message %v", m["msg"])
	}
}
