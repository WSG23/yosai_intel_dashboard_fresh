package cache

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"time"

	"github.com/redis/go-redis/v9"
)

type CacheRule struct {
	Path string
	TTL  time.Duration
}

type cachedResponse struct {
	StatusCode int
	Headers    http.Header
	Body       []byte
}

type CachePlugin struct {
	redis *redis.Client
	rules []CacheRule
}

func (c *CachePlugin) Name() string                             { return "api-cache" }
func (c *CachePlugin) Priority() int                            { return 50 }
func (c *CachePlugin) Init(config map[string]interface{}) error { return nil }

func (c *CachePlugin) Process(ctx context.Context, req *http.Request, resp http.ResponseWriter, next http.Handler) {
	var matched *CacheRule
	for _, r := range c.rules {
		if r.Path == req.URL.Path {
			matched = &r
			break
		}
	}
	if matched == nil || req.Method != http.MethodGet {
		next.ServeHTTP(resp, req)
		return
	}

	key := cacheKey(req)
	val, err := c.redis.Get(ctx, key).Result()
	if err == nil {
		var cr cachedResponse
		if json.Unmarshal([]byte(val), &cr) == nil {
			for k, v := range cr.Headers {
				resp.Header()[k] = v
			}
			resp.Header().Set("X-Cache", "HIT")
			resp.WriteHeader(cr.StatusCode)
			resp.Write(cr.Body)
			return
		}
	}

	recorder := httptest.NewRecorder()
	next.ServeHTTP(recorder, req)
	res := recorder.Result()
	body, _ := io.ReadAll(res.Body)
	res.Body.Close()

	data, _ := json.Marshal(cachedResponse{StatusCode: res.StatusCode, Headers: res.Header, Body: body})
	c.redis.Set(ctx, key, data, matched.TTL)

	for k, v := range res.Header {
		resp.Header()[k] = v
	}
	resp.Header().Set("X-Cache", "MISS")
	resp.WriteHeader(res.StatusCode)
	resp.Write(body)
}

func cacheKey(req *http.Request) string {
	h := sha256.Sum256([]byte(req.Method + "|" + req.URL.String()))
	return "cache:" + hex.EncodeToString(h[:])
}
