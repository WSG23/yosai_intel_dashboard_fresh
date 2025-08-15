package registry

import (
	"context"
	"fmt"
	"net"
	"strconv"

	consul "github.com/hashicorp/consul/api"

	xerrors "github.com/WSG23/errors"
)

// ConsulRegistry implements ServiceRegistry using Hashicorp Consul.
type ConsulRegistry struct {
	client *consul.Client
}

// NewConsulRegistry creates a new Consul-backed registry. The address should
// be in host:port form; when empty the default client configuration is used.
func NewConsulRegistry(address string) (*ConsulRegistry, error) {
	cfg := consul.DefaultConfig()
	if address != "" {
		cfg.Address = address
	}
	c, err := consul.NewClient(cfg)
	if err != nil {
		return nil, err
	}
	return &ConsulRegistry{client: c}, nil
}

// RegisterService registers a service instance with Consul.
func (cr *ConsulRegistry) RegisterService(ctx context.Context, name, addr string) error {
	host, portStr, err := net.SplitHostPort(addr)
	if err != nil {
		return err
	}
	port, err := strconv.Atoi(portStr)
	if err != nil {
		return err
	}
	registration := &consul.AgentServiceRegistration{
		Name:    name,
		Address: host,
		Port:    port,
	}
	return cr.client.Agent().ServiceRegister(registration)
}

// DeregisterService removes a service from Consul.
func (cr *ConsulRegistry) DeregisterService(ctx context.Context, name string) error {
	return cr.client.Agent().ServiceDeregister(name)
}

// ResolveService looks up a healthy service instance and returns its address.
func (cr *ConsulRegistry) ResolveService(ctx context.Context, name string) (string, error) {
	services, _, err := cr.client.Health().Service(name, "", true, nil)
	if err != nil {
		return "", err
	}
	if len(services) == 0 {
		return "", xerrors.Errorf("service %s not found", name)
	}
	s := services[0].Service
	return fmt.Sprintf("%s:%d", s.Address, s.Port), nil
}
