package middleware

import (
    "net/http"
    "sync"
    "time"

    "golang.org/x/time/rate"
)

var (
    visitors = make(map[string]*rate.Limiter)
    mu       sync.Mutex
)

func getVisitor(ip string) *rate.Limiter {
    mu.Lock()
    defer mu.Unlock()

    limiter, exists := visitors[ip]
    if !exists {
        // 100 requests per second with burst of 200
        limiter = rate.NewLimiter(100, 200)
        visitors[ip] = limiter

        // Clean up old visitors
        go func() {
            time.Sleep(time.Hour)
            mu.Lock()
            delete(visitors, ip)
            mu.Unlock()
        }()
    }

    return limiter
}

func RateLimit(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        ip := r.RemoteAddr
        limiter := getVisitor(ip)

        if !limiter.Allow() {
            http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
            return
        }

        next.ServeHTTP(w, r)
    })
}
