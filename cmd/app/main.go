package main

import (
        "context"
        "fmt"
        "log"
        "net/http"
        "time"

        "golang.org/x/sync/errgroup"

        "go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"

        "yourmodule/internal/observability"
        "yourmodule/pkg/shutdown"
)

func main() {
        mux := http.NewServeMux()
        mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) })
        observability.RegisterMetrics(mux)
        srv := &http.Server{Addr: ":8080", Handler: otelhttp.NewHandler(mux, "http")}

        root := context.Background()
        ctx, stop := shutdown.Notify(root)
        defer stop()

        tp, err := observability.InitTracer(ctx, "app")
        if err != nil {
                log.Fatalf("tracing init: %v", err)
        }
        defer observability.Shutdown(context.Background(), tp)

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
