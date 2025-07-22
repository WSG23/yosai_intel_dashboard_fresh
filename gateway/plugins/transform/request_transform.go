package transform

import (
	"context"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"

	"gopkg.in/yaml.v3"
)

// Rule defines how to transform a request matching a path.
type Rule struct {
	Path     string            `yaml:"path"`
	Headers  map[string]string `yaml:"headers,omitempty"`
	Query    map[string]string `yaml:"query,omitempty"`
	Body     string            `yaml:"body,omitempty"`
	Response *ResponseRule     `yaml:"response,omitempty"`
}

// ResponseRule defines optional transformation applied to the response.
type ResponseRule struct {
	Headers map[string]string `yaml:"headers,omitempty"`
	Body    string            `yaml:"body,omitempty"`
}

// RequestTransformPlugin modifies requests according to rules.
type RequestTransformPlugin struct {
	rules []Rule
}

func (r *RequestTransformPlugin) Name() string  { return "request-transform" }
func (r *RequestTransformPlugin) Priority() int { return 40 }

// Init loads rules from config/gateway.yaml. Config parameter is unused.
func (r *RequestTransformPlugin) Init(_ map[string]interface{}) error {
	data, err := os.ReadFile("gateway/config/gateway.yaml")
	if err != nil {
		return err
	}
	var cfg struct {
		Gateway struct {
			Plugins []struct {
				Name    string `yaml:"name"`
				Enabled bool   `yaml:"enabled"`
				Config  struct {
					Rules []Rule `yaml:"rules"`
				} `yaml:"config"`
			} `yaml:"plugins"`
		} `yaml:"gateway"`
	}
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return err
	}
	for _, p := range cfg.Gateway.Plugins {
		if p.Name == "request-transform" && p.Enabled {
			r.rules = p.Config.Rules
			break
		}
	}
	return nil
}

func (r *RequestTransformPlugin) Process(ctx context.Context, req *http.Request, resp http.ResponseWriter, next http.Handler) {
	var matched *Rule
	for i := range r.rules {
		if r.rules[i].Path == req.URL.Path {
			matched = &r.rules[i]
			break
		}
	}
	if matched == nil {
		next.ServeHTTP(resp, req)
		return
	}

	// modify headers
	for k, v := range matched.Headers {
		req.Header.Set(k, v)
	}
	// modify query params
	if len(matched.Query) > 0 {
		q := req.URL.Query()
		for k, v := range matched.Query {
			q.Set(k, v)
		}
		req.URL.RawQuery = q.Encode()
	}
	// modify body
	if matched.Body != "" {
		req.Body = io.NopCloser(strings.NewReader(matched.Body))
		req.ContentLength = int64(len(matched.Body))
	}

	if matched.Response != nil {
		// capture response
		recorder := httptest.NewRecorder()
		next.ServeHTTP(recorder, req)
		res := recorder.Result()
		body, _ := io.ReadAll(res.Body)
		res.Body.Close()

		if matched.Response.Body != "" {
			body = []byte(matched.Response.Body)
		}
		for k, v := range res.Header {
			resp.Header()[k] = v
		}
		for k, v := range matched.Response.Headers {
			resp.Header().Set(k, v)
		}
		resp.WriteHeader(res.StatusCode)
		resp.Write(body)
		return
	}

	next.ServeHTTP(resp, req)
}
