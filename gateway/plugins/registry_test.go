package plugins

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
)

type testPlugin struct {
	name     string
	priority int
	called   *int
}

func (t *testPlugin) Name() string                        { return t.name }
func (t *testPlugin) Priority() int                       { return t.priority }
func (t *testPlugin) Init(_ map[string]interface{}) error { return nil }
func (t *testPlugin) Process(ctx context.Context, req *http.Request, resp http.ResponseWriter, next http.Handler) {
	*t.called = *t.called + 1
	next.ServeHTTP(resp, req)
}

func TestRegistryOrder(t *testing.T) {
	var a, b int
	reg := &PluginRegistry{}
	reg.Register(&testPlugin{name: "a", priority: 20, called: &a})
	reg.Register(&testPlugin{name: "b", priority: 10, called: &b})

	final := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {})
	handler := reg.BuildMiddlewareChain(final)
	req := httptest.NewRequest("GET", "/", nil)
	rr := httptest.NewRecorder()
	handler.ServeHTTP(rr, req)

	if b != 1 || a != 1 {
		t.Fatalf("plugins not executed in priority order")
	}
}
