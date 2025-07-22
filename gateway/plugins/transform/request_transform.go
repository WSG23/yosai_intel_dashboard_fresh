package transform

import (
	"bytes"
	"context"
	"io"
	"net/http"
	"net/http/httptest"
)

type TransformPlugin struct {
	rules []TransformRule
}

type TransformRule struct {
	Path              string
	AddHeaders        map[string]string
	RemoveHeaders     []string
	RenameHeaders     map[string]string
	AddQuery          map[string]string
	RemoveQuery       []string
	BodyTransform     func([]byte) ([]byte, error)
	ResponseTransform func([]byte) ([]byte, error)
}

func (t *TransformPlugin) Name() string                             { return "request-transform" }
func (t *TransformPlugin) Priority() int                            { return 40 }
func (t *TransformPlugin) Init(config map[string]interface{}) error { return nil }

func (t *TransformPlugin) findRule(req *http.Request) *TransformRule {
	for i := range t.rules {
		if t.rules[i].Path == req.URL.Path {
			return &t.rules[i]

		}
	}
	return nil
}

func (t *TransformPlugin) Process(ctx context.Context, req *http.Request, resp http.ResponseWriter, next http.Handler) {
	rule := t.findRule(req)
	if rule == nil {

		next.ServeHTTP(resp, req)
		return
	}

	for k, v := range rule.AddHeaders {
		req.Header.Set(k, v)
	}
	for _, h := range rule.RemoveHeaders {
		req.Header.Del(h)
	}
	for old, newKey := range rule.RenameHeaders {
		if val := req.Header.Get(old); val != "" {
			req.Header.Set(newKey, val)
			req.Header.Del(old)
		}
	}

	query := req.URL.Query()
	for k, v := range rule.AddQuery {
		query.Set(k, v)
	}
	for _, q := range rule.RemoveQuery {
		query.Del(q)
	}
	req.URL.RawQuery = query.Encode()

	if rule.BodyTransform != nil && req.Body != nil {
		body, _ := io.ReadAll(req.Body)
		req.Body.Close()
		transformed, err := rule.BodyTransform(body)
		if err == nil {
			req.Body = io.NopCloser(bytes.NewReader(transformed))
			req.ContentLength = int64(len(transformed))
		} else {
			req.Body = io.NopCloser(bytes.NewReader(body))
		}
	}

	if rule.ResponseTransform != nil {
		recorder := httptest.NewRecorder()
		next.ServeHTTP(recorder, req)
		result := recorder.Result()
		body, _ := io.ReadAll(result.Body)
		result.Body.Close()
		if transformed, err := rule.ResponseTransform(body); err == nil {
			body = transformed
		}
		for k, v := range result.Header {
			resp.Header()[k] = v
		}
		resp.WriteHeader(result.StatusCode)

		resp.Write(body)
		return
	}

	next.ServeHTTP(resp, req)
}
