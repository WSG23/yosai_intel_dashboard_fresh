package registry

import "context"

// ServiceRegistry provides service discovery and registration.
type ServiceRegistry interface {
	// RegisterService registers a service name with its network address
	// in host:port form.
	RegisterService(ctx context.Context, name, address string) error
	// DeregisterService removes a previously registered service.
	DeregisterService(ctx context.Context, name string) error
	// ResolveService returns the network address for the given service.
	ResolveService(ctx context.Context, name string) (string, error)
}
