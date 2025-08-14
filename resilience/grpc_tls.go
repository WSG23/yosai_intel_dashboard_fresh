package resilience

import (
	"crypto/tls"
	"crypto/x509"
	"os"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"
)

// DialTLS creates a gRPC client connection using mutual TLS.
func DialTLS(target, certFile, keyFile, caFile string, opts ...grpc.DialOption) (*grpc.ClientConn, error) {
	cert, err := tls.LoadX509KeyPair(certFile, keyFile)
	if err != nil {
		return nil, err
	}
	ca, err := os.ReadFile(caFile)
	if err != nil {
		return nil, err
	}
	pool := x509.NewCertPool()
	if !pool.AppendCertsFromPEM(ca) {
		return nil, err
	}
	cfg := &tls.Config{Certificates: []tls.Certificate{cert}, RootCAs: pool}
	creds := credentials.NewTLS(cfg)
	return grpc.Dial(target, append(opts, grpc.WithTransportCredentials(creds))...)
}
