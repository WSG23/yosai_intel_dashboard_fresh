package plugins

import (
	"context"
	"net/http"
	"sort"
	"sync"
)

type Plugin interface {
	Name() string
	Priority() int
	Init(config map[string]interface{}) error
	Process(ctx context.Context, req *http.Request, resp http.ResponseWriter, next http.Handler)
}

type PluginRegistry struct {
	plugins []Plugin
	mu      sync.RWMutex
}

func (pr *PluginRegistry) Register(p Plugin) {
	pr.mu.Lock()
	defer pr.mu.Unlock()
	pr.plugins = append(pr.plugins, p)
	sort.Slice(pr.plugins, func(i, j int) bool {
		return pr.plugins[i].Priority() < pr.plugins[j].Priority()
	})
}

func (pr *PluginRegistry) BuildMiddlewareChain(final http.Handler) http.Handler {
	pr.mu.RLock()
	defer pr.mu.RUnlock()
	handler := final
	for i := len(pr.plugins) - 1; i >= 0; i-- {
		plugin := pr.plugins[i]
		next := handler
		handler = http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			plugin.Process(r.Context(), r, w, next)
		})
	}
	return handler
}
