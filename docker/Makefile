SHELL := /bin/bash
IMAGE_PREFIX ?= yosai
BASE_IMAGE := $(IMAGE_PREFIX)-base
APP_IMAGE := $(IMAGE_PREFIX)-app
GATEWAY_IMAGE := $(IMAGE_PREFIX)-gateway
MODEL_IMAGE := $(IMAGE_PREFIX)-model-serving

.PHONY: base app gateway model-serving all

base:
	docker build -f Dockerfile.base -t $(BASE_IMAGE) ..

app: base
	docker build -f Dockerfile.app --build-arg BASE_IMAGE=$(BASE_IMAGE) -t $(APP_IMAGE) ..

gateway:
	docker build -f Dockerfile.gateway -t $(GATEWAY_IMAGE) ..

model-serving: base
	docker build -f Dockerfile.model-serving --build-arg BASE_IMAGE=$(BASE_IMAGE) -t $(MODEL_IMAGE) ..

all: base app gateway model-serving
