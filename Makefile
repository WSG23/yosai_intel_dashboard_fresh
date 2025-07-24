BROKERS ?= localhost:9092
PROM_URL ?= http://localhost:9090
RATE ?= 50
DURATION ?= 60

CLI ?= python -m tools.ops_cli

.PHONY: load-test validate build test deploy format lint clean \
build-all test-all deploy-all logs deprecation-docs \
proto-python proto-go proto-all

load-test:
	python tools/load_test.py --brokers $(BROKERS) --prom-url $(PROM_URL) --rate $(RATE) --duration $(DURATION)

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

deprecation-docs:
	python scripts/generate_deprecation_docs.py

clean:
        $(CLI) clean

PROTOS := $(wildcard proto/*.proto)

proto-python:
	python -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. $(PROTOS)

proto-go:
	protoc -I proto --go_out=. --go-grpc_out=. $(PROTOS)

proto-all: proto-python proto-go

