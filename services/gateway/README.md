# Yōsai Gateway

This module provides the HTTP gateway service for the Yōsai Intel Dashboard.

## Swagger / OpenAPI

Swagger documentation is generated using [swaggo](https://github.com/swaggo/swag).

### Regenerate documentation

```bash
cd gateway
swag init -g cmd/gateway/main.go -o docs
```

### Swagger UI

The gateway serves Swagger UI at `/swagger/` when running in development mode.

```
YOSAI_ENV=development go run cmd/gateway/main.go
# Visit http://localhost:8080/swagger/index.html
```
