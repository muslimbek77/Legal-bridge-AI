.PHONY: help install dev build run test clean docker-up docker-down migrate

# Colors
GREEN=\033[0;32m
NC=\033[0m # No Color

help: ## Show this help
	@echo "Legal Bridge AI - Makefile Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# Development
install: ## Install all dependencies
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

dev-backend: ## Run backend in development mode
	cd backend && python manage.py runserver

dev-frontend: ## Run frontend in development mode
	cd frontend && npm run dev

dev-celery: ## Run celery worker
	cd backend && celery -A config worker -l info

dev: ## Run all services in development mode
	make -j3 dev-backend dev-frontend dev-celery

# Database
migrate: ## Run database migrations
	cd backend && python manage.py migrate

makemigrations: ## Create new migrations
	cd backend && python manage.py makemigrations

createsuperuser: ## Create admin user
	cd backend && python manage.py createsuperuser

loaddata: ## Load initial data
	cd backend && python manage.py loaddata initial_data

# Docker
docker-build: ## Build docker images
	docker-compose build

docker-up: ## Start all containers
	docker-compose up -d

docker-down: ## Stop all containers
	docker-compose down

docker-logs: ## View container logs
	docker-compose logs -f

docker-shell-backend: ## Open shell in backend container
	docker-compose exec backend bash

docker-shell-db: ## Open shell in database container
	docker-compose exec db psql -U legalbridge

docker-migrate: ## Run migrations in docker
	docker-compose exec backend python manage.py migrate

# Testing
test: ## Run all tests
	cd backend && pytest
	cd frontend && npm test

test-backend: ## Run backend tests
	cd backend && pytest -v

test-coverage: ## Run tests with coverage
	cd backend && pytest --cov=. --cov-report=html

lint: ## Run linters
	cd backend && flake8 .
	cd frontend && npm run lint

# Build
build: ## Build for production
	cd frontend && npm run build

# Clean
clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	rm -rf frontend/dist
	rm -rf backend/staticfiles
	rm -rf htmlcov

# Production
prod-deploy: ## Deploy to production
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

prod-logs: ## View production logs
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
