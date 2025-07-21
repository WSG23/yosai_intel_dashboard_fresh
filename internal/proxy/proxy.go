package proxy

import (
    "io"
    "net/http"
    "net/url"
    "time"
)

type ServiceProxy struct {
    target *url.URL
    client *http.Client
}

func New(targetURL string) *ServiceProxy {
    target, _ := url.Parse("http://" + targetURL)
    return &ServiceProxy{
        target: target,
        client: &http.Client{
            Timeout: 30 * time.Second,
        },
    }
}

func (p *ServiceProxy) Handle(w http.ResponseWriter, r *http.Request) {
    // Build target URL
    targetURL := *p.target
    targetURL.Path = r.URL.Path
    targetURL.RawQuery = r.URL.RawQuery

    // Create proxy request
    proxyReq, err := http.NewRequest(r.Method, targetURL.String(), r.Body)
    if err != nil {
        http.Error(w, "Bad gateway", http.StatusBadGateway)
        return
    }

    // Copy headers
    for key, values := range r.Header {
        for _, value := range values {
            proxyReq.Header.Add(key, value)
        }
    }

    // Add X-Forwarded headers
    proxyReq.Header.Set("X-Forwarded-For", r.RemoteAddr)
    proxyReq.Header.Set("X-Forwarded-Host", r.Host)
    proxyReq.Header.Set("X-Forwarded-Proto", "http")

    // Execute request
    resp, err := p.client.Do(proxyReq)
    if err != nil {
        http.Error(w, "Service unavailable", http.StatusServiceUnavailable)
        return
    }
    defer resp.Body.Close()

    // Copy response headers
    for key, values := range resp.Header {
        for _, value := range values {
            w.Header().Add(key, value)
        }
    }

    // Write status code
    w.WriteHeader(resp.StatusCode)

    // Copy response body
    io.Copy(w, resp.Body)
}
