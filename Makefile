BROKERS ?= localhost:9092
PROM_URL ?= http://localhost:9090
RATE ?= 50
DURATION ?= 60

CLI ?= python3 -m tools.ops_cli

DOCKER_COMPOSE := $(shell command -v docker-compose >/dev/null 2>&1 && echo docker-compose || echo "docker compose")
ENV_VARS = $(shell [ -f .env ] && grep -v '^#' .env | xargs)

.PHONY: load-test load-tests validate build test deploy format lint security clean \
build-all test-all deploy-all logs deprecation-docs \
proto-python proto-go proto-all docs test-quick test-cov \
infra-up infra-down infra-logs

load-test:
	python3 tools/load_test.py --brokers $(BROKERS) --prom-url $(PROM_URL) --rate $(RATE) --duration $(DURATION)

load-tests:
	./load-tests/run_k6.sh

validate:
	$(CLI) validate-config

build:
	$(CLI) build

test:
	$(CLI) test

deploy:
	$(CLI) deploy

build-all:
	$(CLI) build-all

test-all:
	$(CLI) test-all

deploy-all:
	$(CLI) deploy-all

logs:
	$(CLI) logs $(service)

format:
	$(CLI) format

lint:
	$(CLI) lint

security:
	$(CLI) security

generate-config-proto:
	protoc --python_out=config/generated --pyi_out=config/generated protobuf/config/schema/config.proto
	protoc --go_out=go/config/generated protobuf/config/schema/config.proto

deprecation-docs:
	python3 scripts/generate_deprecation_docs.py

docs:
	python3 scripts/generate_docs_portal.py

clean:
	$(CLI) clean

PROTOS := $(wildcard proto/*.proto)

proto-python:
	python3 -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. $(PROTOS)

proto-go:
	protoc -I proto --go_out=. --go-grpc_out=. $(PROTOS)

proto-all: proto-python proto-go


docs:
	cd api/openapi && go run .
	python3 scripts/generate_fastapi_openapi.py


# Backend testing targets
test-quick:
	cd services && pytest --no-cov
	cd api && pytest --no-cov

test-cov:
	cd services && pytest
	cd api && pytest --cov-report=html

infra-up:
	docker compose -f dev/docker-compose.dev.yml up -d

infra-down:
	docker compose -f dev/docker-compose.dev.yml down

infra-logs:
	docker compose -f dev/docker-compose.dev.yml logs -f

dev:
	@mkdir -p logs
	@if [ -f deploy/local/docker-compose.dev.yml ]; then \
	        $(ENV_VARS) $(DOCKER_COMPOSE) -f deploy/local/docker-compose.dev.yml up -d; \
	else \
	        $(ENV_VARS) docker run -d --name yosai-postgres -e POSTGRES_PASSWORD=$${POSTGRES_PASSWORD:-postgres} -p 5432:5432 postgres:15; \
	        $(ENV_VARS) docker run -d --name yosai-redis -p 6379:6379 redis:7; \
	        $(ENV_VARS) docker run -d --name yosai-kafka -p 9092:9092 -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 confluentinc/cp-kafka:latest; \
	fi
	@$(ENV_VARS) nohup go run ./gateway/cmd/gateway > logs/gateway.log 2>&1 & echo $$! > logs/gateway.pid
	@$(ENV_VARS) nohup go run ./yosai_intel_dashboard/src/services/event_processing/cmd/processor > logs/event_processor.log 2>&1 & echo $$! > logs/event_processor.pid
	@$(ENV_VARS) nohup uvicorn yosai_intel_dashboard.src.services.analytics_microservice.app:app --host 0.0.0.0 --port 8000 > logs/analytics.log 2>&1 & echo $$! > logs/analytics.pid
	@$(ENV_VARS) nohup npm start > logs/frontend.log 2>&1 & echo $$! > logs/frontend.pid
	@echo "API Gateway:  http://localhost:8080"
	@echo "Analytics:    http://localhost:8000"
	@echo "Frontend:     http://localhost:3000"

stop:
	@if [ -f deploy/local/docker-compose.dev.yml ]; then \
	        $(DOCKER_COMPOSE) -f deploy/local/docker-compose.dev.yml down; \
	else \
	        docker rm -f yosai-postgres yosai-redis yosai-kafka >/dev/null 2>&1 || true; \
	fi
	@for svc in gateway event_processor analytics frontend; do \
	        if [ -f logs/$$svc.pid ]; then \
	                kill $$(cat logs/$$svc.pid) 2>/dev/null || true; \
	                rm -f logs/$$svc.pid; \
	        fi; \
	done
	@echo "Local stack stopped"

.PHONY: dev stop

