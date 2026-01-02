# Makefile for StealthCrawler v17

.PHONY: help install test lint clean build run docker-build docker-up docker-down

# Default target
help:
	@echo "StealthCrawler v17 - Makefile Commands"
	@echo "======================================"
	@echo "install       - Install dependencies"
	@echo "test          - Run tests"
	@echo "test-cov      - Run tests with coverage"
	@echo "lint          - Run linters"
	@echo "clean         - Clean build artifacts"
	@echo "build         - Build Docker image"
	@echo "run           - Run crawler locally"
	@echo "docker-build  - Build Docker images"
	@echo "docker-up     - Start Docker compose stack"
	@echo "docker-down   - Stop Docker compose stack"
	@echo "docker-logs   - View Docker logs"

# Install dependencies
install:
	pip install -r requirements.txt
	playwright install chromium

# Run tests
test:
	pytest tests/ -v

# Run tests with coverage
test-cov:
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

# Run linters
lint:
	@echo "Running linters..."
	-flake8 . --max-line-length=120 --exclude=venv,env,.venv
	-pylint *.py --max-line-length=120
	@echo "Linting complete"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage
	@echo "Clean complete"

# Build Docker image
build:
	docker build -t stealth-crawler:v17 .

# Run crawler locally
run:
	python main.py crawl --help

# Docker compose build
docker-build:
	docker-compose build

# Docker compose up
docker-up:
	docker-compose up -d

# Docker compose down
docker-down:
	docker-compose down

# Docker compose logs
docker-logs:
	docker-compose logs -f

# Quick start
quickstart: install
	@echo "StealthCrawler v17 installed successfully!"
	@echo "Run 'python main.py --help' to get started"

# Development setup
dev-setup: install
	pip install pytest pytest-asyncio pytest-cov flake8 pylint black

# Format code
format:
	black . --line-length=120

# Security check
security:
	pip install safety
	safety check

# Update dependencies
update-deps:
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt
