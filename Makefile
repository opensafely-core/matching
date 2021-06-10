SHELL := /bin/bash

define USAGE
Run commands for a project

Commands:
	format    Runs black and isort over all python files
	lint      Lint all python files using flake8
	typehint  Runs mypy over code base with --ignore-missing-imports flag

endef

export USAGE

help:
	@echo "$$USAGE"

.PHONY: lint
lint:
	@echo "Running flake8" && \
		flake8 \
		|| exit 1

.PHONY: format
format:
	@echo "Running black" && \
		black --check . && \
		echo "Running isort" && \
		isort . \
		|| exit 1

.PHONY: typehint
typehint:
	mypy --ignore-missing-imports --exclude='venv/' ./

IMAGE_NAME=local-matching
.PHONY: build
build:
	docker build . -t $(IMAGE_NAME)

.PHONY: test-docker
test-docker: build
	docker run --rm -v tests:/workspace $(IMAGE_NAME) test_data/input.csv --config test_json/test1_config.json
