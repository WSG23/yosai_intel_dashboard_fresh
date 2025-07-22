package proxy

import (
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
)

// NewProxy returns a reverse proxy to the target service.
func NewProxy() (*httputil.ReverseProxy, error) {
	host := os.Getenv("APP_HOST")
	if host == "" {
		host = "app"
	}
	port := os.Getenv("APP_PORT")
	if port == "" {
		port = "8050"
	}
	target, err := url.Parse("http://" + host + ":" + port)
	if err != nil {
		return nil, err
	}
	p := httputil.NewSingleHostReverseProxy(target)
	orig := p.Director
	p.Director = func(req *http.Request) {
		auth := req.Header.Get("Authorization")
		orig(req)
		if auth != "" {
			req.Header.Set("Authorization", auth)
		}
	}
	return p, nil
}
