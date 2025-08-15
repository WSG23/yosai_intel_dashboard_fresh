package proxy

import (
	"net/http/httputil"
	"net/url"
	"os"
	"strings"

	lb "github.com/WSG23/yosai-gateway/loadbalancer"
)

// NewProxy returns a reverse proxy to the target service.
func NewProxy() (*httputil.ReverseProxy, error) {
	var urls []*url.URL
	if backends := os.Getenv("APP_BACKENDS"); backends != "" {
		for _, b := range strings.Split(backends, ",") {
			b = strings.TrimSpace(b)
			if b == "" {
				continue
			}
			if !strings.Contains(b, "://") {
				b = "http://" + b
			}
			u, err := url.Parse(b)
			if err != nil {
				return nil, err
			}
			urls = append(urls, u)
		}
	} else {
		host := os.Getenv("APP_HOST")
		if host == "" {
			host = "app"
		}
		port := os.Getenv("APP_PORT")
		if port == "" {
			port = "8050"
		}
		u, err := url.Parse("http://" + host + ":" + port)
		if err != nil {
			return nil, err
		}
		urls = append(urls, u)
	}

	balancer := lb.NewAdvanced(urls)

	p := &httputil.ReverseProxy{
		Director:       balancer.Director,
		ModifyResponse: balancer.ModifyResponse,
		ErrorHandler:   balancer.ErrorHandler,
	}
	p.Transport = newTracingTransport(p.Transport)
	return p, nil
}
