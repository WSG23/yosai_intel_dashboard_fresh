package main

import (
	"encoding/json"
	"log"
	"os"

	"github.com/getkin/kin-openapi/openapi3"
)

func main() {
	loader := openapi3.NewLoader()
	doc, err := loader.LoadFromFile("yosai-api-v2.yaml")
	if err != nil {
		log.Fatalf("load spec: %v", err)
	}
	if err := doc.Validate(loader.Context); err != nil {
		log.Fatalf("validate: %v", err)
	}

	data, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		log.Fatalf("marshal: %v", err)
	}

	out := "../../docs/openapi.json"
	if err := os.MkdirAll("../../docs", 0755); err != nil {
		log.Fatalf("mkdir docs: %v", err)
	}
	if err := os.WriteFile(out, data, 0644); err != nil {
		log.Fatalf("write openapi.json: %v", err)
	}
}
