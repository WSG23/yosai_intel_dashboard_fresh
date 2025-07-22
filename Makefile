BROKERS ?= localhost:9092
PROM_URL ?= http://localhost:9090
RATE ?= 50
DURATION ?= 60

.PHONY: load-test
load-test:
	python tools/load_test.py --brokers $(BROKERS) --prom-url $(PROM_URL) --rate $(RATE) --duration $(DURATION)
