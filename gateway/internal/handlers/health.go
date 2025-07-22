package handlers

import (
	"net/http"

	"go.opentelemetry.io/otel"
)

func HealthCheck(w http.ResponseWriter, r *http.Request) {
	_, span := otel.Tracer("gateway").Start(r.Context(), "health")
	defer span.End()

	w.WriteHeader(http.StatusOK)
	w.Write([]byte("ok"))
}
