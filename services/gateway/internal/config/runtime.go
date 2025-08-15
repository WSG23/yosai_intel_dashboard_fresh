package config

import (
	"context"
	"os"
	"strings"

	xerrors "github.com/WSG23/errors"
	vault "github.com/hashicorp/vault/api"
)

// Runtime holds configuration values loaded at startup.
type Runtime struct {
	DBHost       string
	DBPort       string
	DBUser       string
	DBName       string
	DBSSLMode    string
	DBPassword   string
	KafkaBrokers string
	JWTSecret    string
}

// Load reads environment variables and Vault secrets once and validates them.
func Load() (*Runtime, error) {
	required := []string{"DB_HOST", "DB_PORT", "DB_USER", "DB_GATEWAY_NAME"}
	var missing []string
	for _, v := range required {
		if os.Getenv(v) == "" {
			missing = append(missing, v)
		}
	}
	if len(missing) > 0 {
		return nil, xerrors.Errorf("missing required environment variables: %s", strings.Join(missing, ", "))
	}

	vclient, err := newVaultClient()
	if err != nil {
		return nil, err
	}

	dbPassword, err := readVaultField(vclient, "secret/data/db#password")
	if err != nil {
		return nil, err
	}

	jwtSecret, err := readVaultField(vclient, "secret/data/jwt#secret")
	if err != nil {
		return nil, err
	}

	brokers := os.Getenv("KAFKA_BROKERS")
	if brokers == "" {
		brokers = "localhost:9092"
	}

	sslMode := os.Getenv("DB_SSLMODE")
	if sslMode == "" {
		sslMode = "require"
	}

	cfg := &Runtime{
		DBHost:       os.Getenv("DB_HOST"),
		DBPort:       os.Getenv("DB_PORT"),
		DBUser:       os.Getenv("DB_USER"),
		DBName:       os.Getenv("DB_GATEWAY_NAME"),
		DBSSLMode:    sslMode,
		DBPassword:   dbPassword,
		KafkaBrokers: brokers,
		JWTSecret:    jwtSecret,
	}
	return cfg, nil
}

func newVaultClient() (*vault.Client, error) {
	cfg := vault.DefaultConfig()
	if err := cfg.ReadEnvironment(); err != nil {
		return nil, err
	}
	c, err := vault.NewClient(cfg)
	if err != nil {
		return nil, err
	}
	token := os.Getenv("VAULT_TOKEN")
	if token == "" {
		return nil, xerrors.Errorf("VAULT_TOKEN not set")
	}
	c.SetToken(token)
	return c, nil
}

func readVaultField(c *vault.Client, path string) (string, error) {
	parts := strings.SplitN(path, "#", 2)
	if len(parts) != 2 {
		return "", xerrors.Errorf("invalid vault path %q", path)
	}
	p, field := parts[0], parts[1]
	secretPath := strings.TrimPrefix(p, "secret/data/")
	s, err := c.KVv2("secret").Get(context.Background(), secretPath)
	if err != nil {
		return "", err
	}
	val, ok := s.Data[field].(string)
	if !ok {
		return "", xerrors.Errorf("field %s not found at %s", field, p)
	}
	return val, nil
}
