# ===========================
# Cortex Backend Makefile - UV Version
# ===========================

# Variables
PYTHON := uv run python
UV := uv
PORT := 8000
HOST := 0.0.0.0

# Colors
GREEN := \033[0;32m
BLUE := \033[0;34m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: help

help: ## Show this help message
	@echo ''
	@echo '${BLUE}Cortex Backend - Available Commands${NC}'
	@echo ''
	@echo '${YELLOW}Setup & Installation:${NC}'
	@grep -E '^(install|setup|init).*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${GREEN}%-20s${NC} %s\n", $$1, $$2}'
	@echo ''
	@echo '${YELLOW}Development:${NC}'
	@grep -E '^(dev|run|shell).*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${GREEN}%-20s${NC} %s\n", $$1, $$2}'
	@echo ''
	@echo '${YELLOW}Services:${NC}'
	@grep -E '^(up|down|restart|logs|ps).*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${GREEN}%-20s${NC} %s\n", $$1, $$2}'
	@echo ''
	@echo '${YELLOW}Database:${NC}'
	@grep -E '^(db-|migrate|migration).*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${GREEN}%-20s${NC} %s\n", $$1, $$2}'
	@echo ''
	@echo '${YELLOW}Testing & Quality:${NC}'
	@grep -E '^(test|lint|format|check|typecheck).*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${GREEN}%-20s${NC} %s\n", $$1, $$2}'
	@echo ''
	@echo '${YELLOW}Utilities:${NC}'
	@grep -E '^(clean|backup|restore|health|docs).*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${GREEN}%-20s${NC} %s\n", $$1, $$2}'
	@echo ''

# =============================================================================
# Setup & Installation
# =============================================================================

install: ## Install dependencies with uv
	$(UV) sync
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

setup: ## Complete setup (install deps, init db, migrate)
	@echo "$(BLUE)Setting up Cortex backend...$(NC)"
	$(UV) sync
	docker-compose up -d postgres redis
	@echo "$(YELLOW)Waiting for database to be ready...$(NC)"
	@sleep 5
	$(PYTHON) scripts/init_db.py
	$(UV) run alembic upgrade head
	@echo "$(GREEN)✅ Setup complete!$(NC)"

init: setup ## Alias for setup

# =============================================================================
# Development
# =============================================================================

dev: ## Run development server with auto-reload
	$(UV) run uvicorn services.gateway.main:app --reload --host $(HOST) --port $(PORT)

dev-auth: ## Run auth service in development mode
	$(UV) run uvicorn services.auth.main:app --reload --host $(HOST) --port 8001

dev-financial: ## Run financial service in development mode
	$(PYTHON) -m services.financial.main

dev-hr: ## Run HR service in development mode
	$(PYTHON) -m services.hr.main

dev-legal: ## Run legal service in development mode
	$(PYTHON) -m services.legal.main

dev-procurement: ## Run procurement service in development mode
	$(PYTHON) -m services.procurement.main

dev-documents: ## Run documents service in development mode
	$(PYTHON) -m services.documents.main

dev-ai: ## Run AI service in development mode
	$(PYTHON) -m services.ai.main

run: ## Run production server
	$(UV) run uvicorn services.gateway.main:app --host $(HOST) --port $(PORT)

shell: ## Open Python shell
	$(UV) run python

# =============================================================================
# Docker Services Management
# =============================================================================

up: ## Start all services with Docker Compose
	docker-compose up -d
	@echo "$(GREEN)✅ All services started$(NC)"

up-dev: ## Start services in development mode (with logs)
	docker-compose up

down: ## Stop all services
	docker-compose down
	@echo "$(YELLOW)⚠️  All services stopped$(NC)"

restart: ## Restart all services
	docker-compose restart
	@echo "$(GREEN)✅ All services restarted$(NC)"

logs: ## Show logs for all services
	docker-compose logs -f

logs-gateway: ## Show gateway logs
	docker-compose logs -f gateway

logs-auth: ## Show auth service logs
	docker-compose logs -f auth-service

logs-financial: ## Show financial service logs
	docker-compose logs -f financial-service

logs-db: ## Show database logs
	docker-compose logs -f postgres

logs-redis: ## Show Redis logs
	docker-compose logs -f redis

ps: ## Show status of all services
	docker-compose ps

# =============================================================================
# Database Management
# =============================================================================

db-init: ## Initialize database with extensions
	$(PYTHON) scripts/init_db.py
	@echo "$(GREEN)✅ Database initialized$(NC)"

db-up: ## Start PostgreSQL and Redis
	docker-compose up -d postgres redis
	@echo "$(GREEN)✅ Database services started$(NC)"

db-down: ## Stop database services
	docker-compose stop postgres redis
	@echo "$(YELLOW)⚠️  Database services stopped$(NC)"

db-reset: db-down db-up migrate ## Reset database
	@echo "$(GREEN)✅ Database reset complete$(NC)"

db-shell: ## Connect to PostgreSQL shell
	docker-compose exec postgres psql -U cortex_user -d cortex_db

db-shell-auth: ## Connect to auth database shell
	docker-compose exec postgres psql -U authuser -d auth_db

redis-shell: ## Connect to Redis CLI
	docker-compose exec redis redis-cli

# =============================================================================
# Migrations
# =============================================================================

migrate: ## Run database migrations
	$(UV) run alembic upgrade head
	@echo "$(GREEN)✅ Migrations applied$(NC)"

migrate-auth: ## Run auth service migrations
	$(UV) run alembic -c services/auth/alembic.ini upgrade head
	@echo "$(GREEN)✅ Auth migrations applied$(NC)"

migration: ## Create a new migration (usage: make migration m="your message")
ifndef m
	$(error m must be defined, e.g., make migration m="add user table")
endif
	$(UV) run alembic revision --autogenerate -m "$(m)"
	@echo "$(GREEN)✅ Migration created: $(m)$(NC)"

migrate-down: ## Rollback last migration
	$(UV) run alembic downgrade -1
	@echo "$(YELLOW)⚠️  Rolled back last migration$(NC)"

migrate-history: ## Show migration history
	$(UV) run alembic history

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests with coverage
	$(UV) run pytest tests -v --cov=services --cov-report=term-missing

test-auth: ## Run auth service tests
	$(UV) run pytest services/auth/tests -v --cov=services.auth --cov-report=term-missing

test-fast: ## Run quick tests (stop on first failure)
	$(UV) run pytest tests -x

test-unit: ## Run unit tests only
	$(UV) run pytest tests/unit -v

test-integration: ## Run integration tests
	$(UV) run pytest tests/integration -v

test-cov: ## Run tests with HTML coverage report
	$(UV) run pytest --cov=services --cov-report=html --cov-report=term
	@echo "$(GREEN)✅ Coverage report generated in htmlcov/$(NC)"

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run linting with ruff
	$(UV) run ruff check services tests

lint-fix: ## Fix linting issues automatically
	$(UV) run ruff check services tests --fix
	@echo "$(GREEN)✅ Linting issues fixed$(NC)"

format: ## Format code with ruff
	$(UV) run ruff format services tests
	@echo "$(GREEN)✅ Code formatted$(NC)"

typecheck: ## Run type checking with mypy
	$(UV) run mypy services

check: lint typecheck ## Run all quality checks
	@echo "$(GREEN)✅ All checks passed$(NC)"

pre-commit: format lint-fix test ## Run pre-commit checks
	@echo "$(GREEN)✅ Pre-commit checks passed$(NC)"

# =============================================================================
# Utilities
# =============================================================================

clean: ## Clean up containers, volumes, and cache
	docker-compose down -v 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf htmlcov 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

build: ## Build Docker images
	docker-compose build
	@echo "$(GREEN)✅ Docker images built$(NC)"

pull: ## Pull latest Docker images
	docker-compose pull
	@echo "$(GREEN)✅ Docker images updated$(NC)"

health: ## Check health of all services
	@curl -s http://localhost:8000/health | python -m json.tool || echo "$(RED)Gateway not running$(NC)"
	@curl -s http://localhost:8001/health | python -m json.tool || echo "$(RED)Auth service not running$(NC)"

docs: ## Open API documentation
	@open http://localhost:8000/docs 2>/dev/null || echo "$(BLUE)Open http://localhost:8000/docs$(NC)"

docs-auth: ## Open Auth API documentation
	@open http://localhost:8001/docs 2>/dev/null || echo "$(BLUE)Open http://localhost:8001/docs$(NC)"

kill-port: ## Kill process on port $(PORT) (usage: make kill-port PORT=8001)
	@lsof -ti:$(PORT) | xargs kill -9 2>/dev/null || echo "$(GREEN)No process on port $(PORT)$(NC)"

# =============================================================================
# Database Backup & Restore
# =============================================================================

backup-db: ## Backup database to file
	@mkdir -p backups
	docker-compose exec postgres pg_dump -U cortex_user cortex_db > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Database backed up to backups/backup_$(shell date +%Y%m%d_%H%M%S).sql$(NC)"

backup-auth-db: ## Backup auth database
	@mkdir -p backups
	docker-compose exec postgres pg_dump -U authuser auth_db > backups/auth_backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Auth database backed up$(NC)"

restore-db: ## Restore database from file (usage: make restore-db FILE=backups/backup.sql)
ifndef FILE
	$(error FILE must be defined, e.g., make restore-db FILE=backups/backup.sql)
endif
	docker-compose exec -T postgres psql -U cortex_user cortex_db < $(FILE)
	@echo "$(GREEN)✅ Database restored from $(FILE)$(NC)"

# =============================================================================
# Docker Cleanup
# =============================================================================

docker-clean: ## Remove all stopped containers and unused images
	docker system prune -f
	@echo "$(GREEN)✅ Docker cleanup complete$(NC)"

docker-clean-all: ## Remove all containers, images, and volumes (CAREFUL!)
	@echo "$(RED)⚠️  WARNING: This will remove ALL Docker resources$(NC)"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker system prune -af --volumes; \
		echo "$(GREEN)✅ All Docker resources removed$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

# =============================================================================
# Shortcuts & Workflows
# =============================================================================

start: db-up migrate dev ## Start database and development server

start-all: up logs ## Start all services with Docker and show logs

stop: down ## Stop all services

reset: clean setup ## Clean everything and setup from scratch

update: install migrate ## Update dependencies and run migrations

.DEFAULT_GOAL := help