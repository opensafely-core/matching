SHELL := /bin/bash

define USAGE
Run commands for a project

Commands:
	format    	Runs black and isort over all python files
	lint      	Lint all python files using flake8
	typehint  	Runs mypy over code base with --ignore-missing-imports flag
	build     	Build docker image
	test-docker	Test Docker image can be built and used

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
build:
	docker build . -t $(IMAGE_NAME)

test-docker: build
	docker run --rm -v :/workspace $(IMAGE_NAME) --cases input_cases.csv --controls input_controls.csv --config tests/test_json/test_json_1.json

