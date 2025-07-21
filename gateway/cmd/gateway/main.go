package main

import (
	"log"
	"net/http"
	"os"

	"github.com/WSG23/yosai-gateway/internal/gateway"
)

func main() {
	g, err := gateway.New()
	if err != nil {
		log.Fatalf("failed to create gateway: %v", err)
	}

	// enable middleware based on env vars
	if os.Getenv("ENABLE_AUTH") == "1" {
		g.UseAuth()
	}
	if os.Getenv("ENABLE_RATELIMIT") == "1" {
		g.UseRateLimit()
	}

	addr := ":8080"
	if port := os.Getenv("PORT"); port != "" {
		addr = ":" + port
	}

	log.Printf("starting gateway on %s", addr)
	if err := http.ListenAndServe(addr, g.Handler()); err != nil {
		log.Fatalf("server error: %v", err)
	}
}
