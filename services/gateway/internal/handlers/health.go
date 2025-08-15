package handlers

import (
	"net/http"

	"go.opentelemetry.io/otel"
)

// HealthCheck provides a simple health status.
//
// @Summary      Health check
// @Description  Returns OK if the service is running
// @Tags         system
// @Produce      plain
// @Success      200  {string}  string  "ok"
// @Router       /health [get]
func HealthCheck(w http.ResponseWriter, r *http.Request) {
	_, span := otel.Tracer("gateway").Start(r.Context(), "health")
	defer span.End()

	w.WriteHeader(http.StatusOK)
	w.Write([]byte("ok"))
}
