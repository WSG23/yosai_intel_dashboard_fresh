package health

import (
	"encoding/json"
	"net/http"
)

// HealthChecker exposes current service health state.
type HealthChecker interface {
	Live() bool
	Ready() bool
	StartupComplete() bool
}

// HealthManager implements HealthChecker and allows state mutation.
type HealthManager struct {
	live            bool
	ready           bool
	startupComplete bool
}

// NewManager returns a new HealthManager with all states false.
func NewManager() *HealthManager { return &HealthManager{} }

func (h *HealthManager) Live() bool            { return h.live }
func (h *HealthManager) Ready() bool           { return h.ready }
func (h *HealthManager) StartupComplete() bool { return h.startupComplete }

func (h *HealthManager) SetLive(v bool)            { h.live = v }
func (h *HealthManager) SetReady(v bool)           { h.ready = v }
func (h *HealthManager) SetStartupComplete(v bool) { h.startupComplete = v }

func writeJSON(w http.ResponseWriter, status string) {
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(map[string]string{"status": status}); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

// Handler returns /health status.
func (h *HealthManager) Handler(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, "ok")
}

// LiveHandler returns liveness.
func (h *HealthManager) LiveHandler(w http.ResponseWriter, _ *http.Request) {
	if h.live {
		writeJSON(w, "ok")
		return
	}
	writeJSON(w, "shutdown")
}

// ReadyHandler returns readiness.
func (h *HealthManager) ReadyHandler(w http.ResponseWriter, _ *http.Request) {
	if h.ready {
		writeJSON(w, "ready")
		return
	}
	w.WriteHeader(http.StatusServiceUnavailable)
	writeJSON(w, "not ready")
}

// StartupHandler returns startup completion state.
func (h *HealthManager) StartupHandler(w http.ResponseWriter, _ *http.Request) {
	if h.startupComplete {
		writeJSON(w, "complete")
		return
	}
	w.WriteHeader(http.StatusServiceUnavailable)
	writeJSON(w, "starting")
}
