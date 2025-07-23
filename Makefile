BROKERS ?= localhost:9092
PROM_URL ?= http://localhost:9090
RATE ?= 50
DURATION ?= 60

CLI ?= python -m tools.ops_cli

.PHONY: load-test validate build test deploy format lint clean

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

format:
	$(CLI) format

lint:
	$(CLI) lint

clean:
	$(CLI) clean

