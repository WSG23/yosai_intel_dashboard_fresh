package admin

import (
	"net/http"
	"time"

	"github.com/gorilla/mux"

	ilog "github.com/WSG23/yosai-gateway/internal/logging"
)

// AuditMiddleware records admin actions for auditing purposes.
func AuditMiddleware(l *ilog.AuditLogger) mux.MiddlewareFunc {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			sr := &statusRecorder{ResponseWriter: w, status: http.StatusOK}
			next.ServeHTTP(sr, r)
			outcome := "success"
			if sr.status >= 400 {
				outcome = "failure"
			}
			_ = l.Log(r.Context(), ilog.AuditLog{
				User:      r.Header.Get("X-User-ID"),
				Timestamp: time.Now().UTC(),
				Action:    r.Method + " " + r.URL.Path,
				Outcome:   outcome,
			})
		})
	}
}

// statusRecorder captures the response status code.
type statusRecorder struct {
	http.ResponseWriter
	status int
}

func (s *statusRecorder) WriteHeader(code int) {
	s.status = code
	s.ResponseWriter.WriteHeader(code)
}
