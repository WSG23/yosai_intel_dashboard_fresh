package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"

	"github.com/getkin/kin-openapi/openapi3"
	"github.com/gorilla/mux"
)

// predefined error codes used across the API
var errorCodes = []string{
	"bad_request",
	"invalid_payload",
	"invalid_plugin",
	"invalid_type",
	"missing_file_id",
	"no_data",
	"no_file",
	"no_file_id",
	"no_file_selected",
	"no_files",
	"not_found",
	"read_error",
	"server_error",
	"unsupported_type",
}

// RegisterErrorCodes adds the ErrorResponse schema with predefined error codes
func RegisterErrorCodes(spec *openapi3.T) {
	codesSchema := openapi3.NewStringSchema().WithEnum(func() []interface{} {
		vals := make([]interface{}, len(errorCodes))
		for i, c := range errorCodes {
			vals[i] = c
		}
		return vals
	}())

	errSchema := openapi3.NewObjectSchema().
		WithProperty("code", codesSchema).
		WithProperty("message", openapi3.NewStringSchema()).
		WithPropertyRef("details", &openapi3.SchemaRef{Ref: "#/components/schemas/ErrorDetails"})
	errSchema.Required = []string{"code", "message"}

	spec.Components.Schemas["ErrorResponse"] = &openapi3.SchemaRef{Value: errSchema}
	spec.Components.Schemas["ErrorDetails"] = &openapi3.SchemaRef{Value: openapi3.NewStringSchema()}
}

// DocumentAccessEventEndpoint documents the POST /events/access endpoint
func DocumentAccessEventEndpoint(spec *openapi3.T) {
	accessEvent := openapi3.NewObjectSchema().
		WithProperty("event_id", openapi3.NewStringSchema()).
		WithProperty("timestamp", openapi3.NewStringSchema().WithFormat("date-time")).
		WithProperty("person_id", openapi3.NewStringSchema()).
		WithProperty("door_id", openapi3.NewStringSchema()).
		WithProperty("access_result", openapi3.NewStringSchema())
	accessEvent.Required = []string{"event_id", "timestamp", "person_id", "door_id", "access_result"}
	spec.Components.Schemas["AccessEvent"] = &openapi3.SchemaRef{Value: accessEvent}

	op := &openapi3.Operation{
		Summary:     "Record an access event",
		Description: "Submit an access control event for processing",
		RequestBody: &openapi3.RequestBodyRef{Value: &openapi3.RequestBody{
			Required: true,
			Content: openapi3.Content{
				"application/json": &openapi3.MediaType{
					Schema: &openapi3.SchemaRef{Ref: "#/components/schemas/AccessEvent"},
				},
			},
		}},
		Responses: openapi3.Responses{
			"202": {Value: openapi3.NewResponse().WithDescription("Accepted")},
			"400": {Value: openapi3.NewResponse().WithDescription("Bad request")},
		},
	}

	pathItem := &openapi3.PathItem{Post: op}
	spec.Paths["/events/access"] = pathItem
}

// walkRoutes populates the OpenAPI spec from a mux.Router
func walkRoutes(r *mux.Router, spec *openapi3.T) {
	r.Walk(func(route *mux.Route, _ *mux.Router, _ []*mux.Route) error {
		path, err := route.GetPathTemplate()
		if err != nil {
			return nil
		}
		methods, err := route.GetMethods()
		if err != nil {
			return nil
		}
		if _, ok := spec.Paths[path]; !ok {
			spec.Paths[path] = &openapi3.PathItem{}
		}
		item := spec.Paths[path]
		for _, m := range methods {
			op := &openapi3.Operation{Summary: path}
			switch m {
			case http.MethodGet:
				item.Get = op
			case http.MethodPost:
				item.Post = op
			case http.MethodPut:
				item.Put = op
			case http.MethodDelete:
				item.Delete = op
			}
		}
		return nil
	})
}

func main() {
	router := mux.NewRouter()
	router.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodGet)
	router.HandleFunc("/metrics", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodGet)
	router.HandleFunc("/events/access", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodPost)

	// API endpoints registered in the Python server
	router.HandleFunc("/v1/csrf-token", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodGet)
	router.HandleFunc("/v1/upload", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodPost)
	router.HandleFunc("/v1/upload/status/{job_id}", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodGet)
	router.HandleFunc("/v1/ai/suggest-devices", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodPost)
	router.HandleFunc("/v1/mappings/columns", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodPost)
	router.HandleFunc("/v1/mappings/devices", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodPost)
	router.HandleFunc("/v1/mappings/save", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodPost)
	router.HandleFunc("/v1/process-enhanced", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodPost)
	router.HandleFunc("/api/v1/settings", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodGet, http.MethodPost, http.MethodPut)
	router.HandleFunc("/v1/plugins/performance", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodGet)
	router.HandleFunc("/v1/plugins/performance/alerts", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodGet, http.MethodPost)
	router.HandleFunc("/v1/plugins/performance/benchmark", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodPost)
	router.HandleFunc("/v1/plugins/performance/config", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodGet, http.MethodPut)
	router.HandleFunc("/api/v1/risk/score", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodPost)
	router.HandleFunc("/api/v1/analytics/patterns", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodGet)
	router.HandleFunc("/api/v1/analytics/sources", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodGet)
	router.HandleFunc("/api/v1/analytics/health", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodGet)
	router.HandleFunc("/api/v1/analytics/all", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodGet)
	router.HandleFunc("/api/v1/analytics/{source_type}", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodGet)
	router.HandleFunc("/api/v1/graphs/chart/{chart_type}", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodGet)
	router.HandleFunc("/api/v1/export/analytics/json", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodGet)
	router.HandleFunc("/api/v1/graphs/available-charts", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodGet)
	router.HandleFunc("/api/v1/export/formats", func(w http.ResponseWriter, r *http.Request) {}).Methods(http.MethodGet)

	spec := &openapi3.T{
		OpenAPI: "3.0.2",
		Info: &openapi3.Info{
			Title:   "Yōsai Intel API",
			Version: "1.0.0",
		},
		Paths: openapi3.Paths{},
	}

	spec.Components = &openapi3.Components{Schemas: openapi3.Schemas{}}

	walkRoutes(router, spec)
	RegisterErrorCodes(spec)
	DocumentAccessEventEndpoint(spec)

	data, err := json.MarshalIndent(spec, "", "  ")
	if err != nil {
		log.Fatalf("marshal: %v", err)
	}

	outDir := "../docs"
	if err := os.MkdirAll(outDir, 0755); err != nil {
		log.Fatalf("mkdir docs: %v", err)
	}
	if err := os.WriteFile(outDir+"/openapi.json", data, 0644); err != nil {
		log.Fatalf("write openapi.json: %v", err)
	}
}
