package logging

import (
	"bytes"
	"encoding/json"
	"io"
	"os"
	"testing"
)

func TestZapLoggerJSON(t *testing.T) {
	r, w, _ := os.Pipe()
	orig := os.Stdout
	os.Stdout = w
	lg, err := NewZapLogger("test", "INFO")
	if err != nil {
		t.Fatal(err)
	}
	lg.Info("hello")
	lg.Logger.Sync()
	w.Close()
	os.Stdout = orig
	data, _ := io.ReadAll(r)
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
