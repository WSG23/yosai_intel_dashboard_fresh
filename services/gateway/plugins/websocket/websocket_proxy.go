package websocket

import (
	"context"
	"net/http"
	"net/url"
	"strings"

	"github.com/gorilla/websocket"
)

// Route defines a websocket route handled by the proxy.
type Route struct {
	Path    string
	Backend string
}

// ProxyPlugin proxies websocket connections to configured backends.
type ProxyPlugin struct {
	routes []Route
}

func (p *ProxyPlugin) Name() string  { return "websocket-proxy" }
func (p *ProxyPlugin) Priority() int { return 5 }

func (p *ProxyPlugin) Init(config map[string]interface{}) error {
	if v, ok := config["routes"].([]interface{}); ok {
		for _, r := range v {
			m, ok := r.(map[string]interface{})
			if !ok {
				continue
			}
			path, _ := m["path"].(string)
			backend, _ := m["backend"].(string)
			if path != "" && backend != "" {
				p.routes = append(p.routes, Route{Path: path, Backend: backend})
			}
		}
	}
	return nil
}

func (p *ProxyPlugin) Process(ctx context.Context, req *http.Request, resp http.ResponseWriter, next http.Handler) {
	if !isWebSocketRequest(req) {
		next.ServeHTTP(resp, req)
		return
	}

	var backend string
	for _, r := range p.routes {
		if r.Path == req.URL.Path {
			backend = r.Backend
			break
		}
	}
	if backend == "" {
		next.ServeHTTP(resp, req)
		return
	}

	up := websocket.Upgrader{CheckOrigin: func(r *http.Request) bool { return true }}
	clientConn, err := up.Upgrade(resp, req, nil)
	if err != nil {
		http.Error(resp, "upgrade failed", http.StatusBadRequest)
		return
	}
	defer clientConn.Close()

	u, err := url.Parse(backend)
	if err != nil {
		return
	}

	backendConn, _, err := websocket.DefaultDialer.Dial(u.String(), nil)
	if err != nil {
		return
	}
	defer backendConn.Close()

	errc := make(chan error, 2)
	go proxyConn(clientConn, backendConn, errc)
	go proxyConn(backendConn, clientConn, errc)
	<-errc
}

func proxyConn(src, dst *websocket.Conn, errc chan error) {
	for {
		mt, msg, err := src.ReadMessage()
		if err != nil {
			errc <- err
			return
		}
		if err = dst.WriteMessage(mt, msg); err != nil {
			errc <- err
			return
		}
	}
}

func isWebSocketRequest(r *http.Request) bool {
	return strings.EqualFold(r.Header.Get("Connection"), "Upgrade") &&
		strings.EqualFold(r.Header.Get("Upgrade"), "websocket")
}
