package main

import (
	"context"
	"log"

	framework "github.com/WSG23/yosai-framework"

	"github.com/WSG23/yosai-event-processing/internal/config"
	"github.com/WSG23/yosai-event-processing/internal/handlers"
	"github.com/WSG23/yosai-event-processing/internal/kafka"
	"github.com/WSG23/yosai-event-processing/internal/repository"
)

func main() {
	b, err := framework.NewServiceBuilder("event-processing", "config/service.yaml")
	if err != nil {
		log.Fatalf("failed to init service builder: %v", err)
	}
	svc, err := b.Build()
	if err != nil {
		log.Fatalf("failed to build service: %v", err)
	}

	cfg, err := config.Load("")
	if err != nil {
		log.Fatalf("failed to load config: %v", err)
	}

	consumer, err := kafka.NewConsumer(cfg.Brokers, cfg.GroupID)
	if err != nil {
		log.Fatalf("kafka error: %v", err)
	}
	defer consumer.Close()

	handler := handlers.NewEventHandler(repository.NewMemoryTokenStore())
	go func() {
		if err := consumer.Consume(context.Background(), []string{cfg.Topic}, handler.HandleMessage); err != nil {
			log.Printf("consumer stopped: %v", err)
			svc.Stop()
		}
	}()

	svc.Start()
}
