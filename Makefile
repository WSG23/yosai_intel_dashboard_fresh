SHELL := /bin/bash
DC := docker compose

.PHONY: up down logs ps
up:       ; @$(DC) up -d --build
down:     ; @$(DC) down -v
logs:     ; @$(DC) logs -f --tail=200
ps:       ; @$(DC) ps

BROKERS ?= localhost:9092
PROM_URL ?= http://localhost:9090
RATE ?= 50
DURATION ?= 60

CLI ?= python3 -m tools.ops_cli

DOCKER_COMPOSE := $(shell command -v docker-compose >/dev/null 2>&1 && echo docker-compose || echo "docker compose")
ENV_VARS = $(shell [ -f .env ] && grep -v '^#' .env | xargs)

.PHONY: load-test load-tests validate build test deploy format lint security clean \
build-all test-all deploy-all cli-logs deprecation-docs \
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

cli-logs:
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
	docker compose up -d

infra-down:
	docker compose down

infra-logs:
	docker compose logs -f

dev:
	docker compose up -d

stop:
	docker compose down

.PHONY: dev stop
