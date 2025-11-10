.PHONY: help install run test docker-build docker-up docker-down clean

help:
	@echo "Available commands:"
	@echo "  make install     - Install dependencies"
	@echo "  make run         - Run the service locally"
	@echo "  make test        - Test the service"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-up   - Start services with Docker Compose"
	@echo "  make docker-down - Stop Docker Compose services"
	@echo "  make clean       - Clean up generated files"

install:
	pip install -r requirements.txt

run:
	python run.py

test:
	python test_service.py

docker-build:
	docker build -t aurora-qa-service .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

