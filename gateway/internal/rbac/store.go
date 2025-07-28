package rbac

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"strings"

	"github.com/redis/go-redis/v9"
)

// PermissionStore abstracts the backend used to retrieve permissions.
type PermissionStore interface {
	Permissions(ctx context.Context, subject string) ([]string, error)
}

// EnvStore loads permissions from environment variables.
type EnvStore struct{}

// Permissions implements PermissionStore for EnvStore.
func (EnvStore) Permissions(ctx context.Context, subject string) ([]string, error) {
	key := "PERMISSIONS_" + strings.ToUpper(subject)
	v := getenv(key)
	if v == "" {
		v = getenv("PERMISSIONS")
	}
	if v == "" {
		return nil, nil
	}
	parts := strings.Split(v, ",")
	perms := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			perms = append(perms, p)
		}
	}
	return perms, nil
}

// RedisStore retrieves permissions from Redis keys of the form
// "<prefix>:<subject>" where the value is a comma separated list.
type RedisStore struct {
	client *redis.Client
	prefix string
}

// NewRedisStore creates a RedisStore using the given client.
func NewRedisStore(client *redis.Client, prefix string) *RedisStore {
	if prefix == "" {
		prefix = "permissions"
	}
	return &RedisStore{client: client, prefix: prefix}
}

func (r *RedisStore) key(subject string) string {
	return fmt.Sprintf("%s:%s", r.prefix, strings.ToLower(subject))
}

// Permissions implements PermissionStore for RedisStore.
func (r *RedisStore) Permissions(ctx context.Context, subject string) ([]string, error) {
	val, err := r.client.Get(ctx, r.key(subject)).Result()
	if err != nil {
		if err == redis.Nil {
			return nil, nil
		}
		return nil, err
	}
	parts := strings.Split(val, ",")
	perms := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			perms = append(perms, p)
		}
	}
	return perms, nil
}

// SQLStore retrieves permissions from a SQL database.
type SQLStore struct {
	db *sql.DB
}

// NewSQLStore creates a SQLStore using the given db handle.
func NewSQLStore(db *sql.DB) *SQLStore { return &SQLStore{db: db} }

// Permissions implements PermissionStore for SQLStore.
func (s *SQLStore) Permissions(ctx context.Context, subject string) ([]string, error) {
	rows, err := s.db.QueryContext(ctx, `
        SELECT p.name
        FROM permissions p
        JOIN role_permissions rp ON rp.permission_id = p.id
        JOIN user_roles ur ON ur.role_id = rp.role_id
        WHERE ur.user_id = $1`, subject)
	if err != nil {
		return nil, err
	}
	defer func() { _ = rows.Close() }()
	var perms []string
	for rows.Next() {
		var name string
		if err := rows.Scan(&name); err != nil {
			return nil, err
		}
		perms = append(perms, name)
	}
	return perms, rows.Err()
}

// getenv allows tests to override environment variable lookup.
var getenv = func(key string) string {
	return os.Getenv(key)
}
