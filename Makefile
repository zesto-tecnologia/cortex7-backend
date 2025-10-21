# Makefile for Cortex Backend

.PHONY: help install setup db-init migrate up down restart logs clean test lint format

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies with Poetry
	poetry install

setup: ## Complete setup (install deps, init db, migrate)
	@echo "Setting up Cortex backend..."
	poetry install
	docker-compose up -d postgres redis
	sleep 5
	poetry run python scripts/init_db.py
	poetry run alembic upgrade head
	@echo "Setup complete!"

db-init: ## Initialize database with extensions
	poetry run python scripts/init_db.py

migrate: ## Run database migrations
	poetry run alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="your message")
	poetry run alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback last migration
	poetry run alembic downgrade -1

migrate-history: ## Show migration history
	poetry run alembic history

up: ## Start all services with Docker Compose
	docker-compose up -d

up-dev: ## Start services in development mode (with logs)
	docker-compose up

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## Show logs for all services
	docker-compose logs -f

logs-gateway: ## Show gateway logs
	docker-compose logs -f gateway

logs-financial: ## Show financial service logs
	docker-compose logs -f financial-service

logs-db: ## Show database logs
	docker-compose logs -f postgres

ps: ## Show status of all services
	docker-compose ps

clean: ## Clean up containers, volumes, and cache
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

test: ## Run tests
	poetry run pytest

test-cov: ## Run tests with coverage
	poetry run pytest --cov=. --cov-report=html --cov-report=term

lint: ## Run linters (flake8, mypy)
	poetry run flake8 .
	poetry run mypy .

format: ## Format code with black and isort
	poetry run black .
	poetry run isort .

shell-db: ## Connect to PostgreSQL shell
	docker-compose exec postgres psql -U cortex_user -d cortex_db

shell-redis: ## Connect to Redis CLI
	docker-compose exec redis redis-cli

dev-gateway: ## Run gateway in development mode
	poetry run uvicorn services.gateway.main:app --reload --port 8000

dev-financial: ## Run financial service in development mode
	poetry run python -m services.financial.main

dev-hr: ## Run HR service in development mode
	poetry run python -m services.hr.main

dev-legal: ## Run legal service in development mode
	poetry run python -m services.legal.main

build: ## Build Docker images
	docker-compose build

pull: ## Pull latest Docker images
	docker-compose pull

health: ## Check health of all services
	@curl -s http://localhost:8000/health | python -m json.tool

# Database backup and restore
backup-db: ## Backup database to file
	@mkdir -p backups
	docker-compose exec postgres pg_dump -U cortex_user cortex_db > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Database backed up to backups/backup_$(shell date +%Y%m%d_%H%M%S).sql"

restore-db: ## Restore database from file (usage: make restore-db FILE=backups/backup.sql)
	docker-compose exec -T postgres psql -U cortex_user cortex_db < $(FILE)
	@echo "Database restored from $(FILE)"

# Docker cleanup
docker-clean: ## Remove all stopped containers and unused images
	docker system prune -f

docker-clean-all: ## Remove all containers, images, and volumes (CAREFUL!)
	docker system prune -af --volumes