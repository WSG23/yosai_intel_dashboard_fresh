package framework

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"
)

// BaseService provides logging, metrics, tracing and signal handling.
type BaseService struct {
	Name   string
	Config Config
	ctx    context.Context
	cancel context.CancelFunc
}

func NewBaseService(name, cfgPath string) (*BaseService, error) {
	cfg, err := LoadConfig(cfgPath)
	if err != nil {
		return nil, err
	}
	ctx, cancel := context.WithCancel(context.Background())
	return &BaseService{Name: name, Config: cfg, ctx: ctx, cancel: cancel}, nil
}

func (s *BaseService) Start() {
	s.setupLogging()
	s.setupMetrics()
	s.setupTracing()
	s.handleSignals()
	log.Printf("service %s started", s.Name)
	<-s.ctx.Done()
	log.Printf("service %s stopped", s.Name)
}

func (s *BaseService) Stop() { s.cancel() }

func (s *BaseService) setupLogging() {
	log.SetOutput(os.Stdout)
}

func (s *BaseService) setupMetrics() {}
func (s *BaseService) setupTracing() {}

func (s *BaseService) handleSignals() {
	ch := make(chan os.Signal, 1)
	signal.Notify(ch, syscall.SIGTERM, syscall.SIGINT)
	go func() {
		<-ch
		s.Stop()
	}()
}
