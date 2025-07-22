package versioning

import (
	"context"
	"fmt"
	"net/http"
	"strings"
	"time"
)

type APIVersion struct {
	Version       string
	Status        VersionStatus
	DeprecatedAt  *time.Time
	SunsetAt      *time.Time
	Documentation string
}

type VersionStatus string

const (
	VersionActive     VersionStatus = "active"
	VersionDeprecated VersionStatus = "deprecated"
	VersionSunset     VersionStatus = "sunset"
)

type VersionManager struct {
	versions       map[string]*APIVersion
	currentVersion string
	handlers       map[string]http.Handler
}

func NewVersionManager() *VersionManager {
	return &VersionManager{
		versions: map[string]*APIVersion{
			"v1": {Version: "v1", Status: VersionDeprecated},
			"v2": {Version: "v2", Status: VersionActive},
		},
		currentVersion: "v2",
		handlers:       make(map[string]http.Handler),
	}
}

func (vm *VersionManager) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		version := extractVersion(r)
		v, ok := vm.versions[version]
		if !ok {
			http.Error(w, fmt.Sprintf("unknown api version %s", version), http.StatusNotFound)
			return
		}
		if v.Status == VersionSunset {
			http.Error(w, fmt.Sprintf("version %s is sunset", version), http.StatusGone)
			return
		}
		if v.Status == VersionDeprecated {
			w.Header().Set("Warning", fmt.Sprintf("299 - version %s is deprecated", version))
		}
		ctx := context.WithValue(r.Context(), apiVersionKey{}, v)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func extractVersion(r *http.Request) string {
	segments := strings.Split(strings.TrimPrefix(r.URL.Path, "/"), "/")
	if len(segments) > 0 {
		return segments[0]
	}
	return ""
}

type apiVersionKey struct{}

func FromContext(ctx context.Context) *APIVersion {
	v, _ := ctx.Value(apiVersionKey{}).(*APIVersion)
	return v
}

func (vm *VersionManager) Handle(version string, h http.Handler) {
	vm.handlers[version] = h
}

func (vm *VersionManager) Handler(version string) (http.Handler, bool) {
	h, ok := vm.handlers[version]
	return h, ok
}
