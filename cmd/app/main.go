package main

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"golang.org/x/sync/errgroup"

	"yourmodule/pkg/shutdown"
)

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) })
	srv := &http.Server{Addr: ":8080", Handler: mux}

	root := context.Background()
	ctx, stop := shutdown.Notify(root)
	defer stop()

	eg, ctx := errgroup.WithContext(ctx)

	// Run server
	eg.Go(func() error {
		fmt.Println("listening on :8080")
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			return err
		}
		return nil
	})

	// Wait for signal/cancel then shutdown gracefully
	eg.Go(func() error {
		<-ctx.Done()
		shctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		return srv.Shutdown(shctx)
	})

	if err := eg.Wait(); err != nil {
		fmt.Println("server exit:", err)
	}
}
