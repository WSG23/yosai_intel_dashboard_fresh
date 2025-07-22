package proxy

import (
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
	p.Transport = newTracingTransport(p.Transport)

	return p, nil
}
