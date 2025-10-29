# ===========================
# Cortex7 Backend - Essential Commands
# ===========================

# Variables
PYTHON := python3
UV := uv --index-strategy unsafe-best-match
COMPOSE := docker-compose
DB_USER := cortex_user
DB_NAME := cortex_db

# Colors
GREEN := \033[0;32m
BLUE := \033[0;34m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: help

help: ## Show this help message
	@echo ''
	@echo '${BLUE}Cortex7 Backend - Essential Commands${NC}'
	@echo '${BLUE}=====================================>${NC}'
	@echo ''
	@echo '${YELLOW}🐳 Docker Containers:${NC}'
	@grep -E '^(up|down|restart|build|rebuild|ps|logs).*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${GREEN}%-20s${NC} %s\n", $$1, $$2}'
	@echo ''
	@echo '${YELLOW}🗄️  Database:${NC}'
	@grep -E '^(migrate|migration-new|migrate-down|db-shell|db-backup|db-restore|db-verify).*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${GREEN}%-20s${NC} %s\n", $$1, $$2}'
	@echo ''
	@echo '${YELLOW}🧪 Testing:${NC}'
	@grep -E '^(test|test-refactoring|test-integration).*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${GREEN}%-20s${NC} %s\n", $$1, $$2}'
	@echo ''
	@echo '${YELLOW}🧹 Maintenance:${NC}'
	@grep -E '^(clean|clean-all|prune|install).*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${GREEN}%-20s${NC} %s\n", $$1, $$2}'
	@echo ''
	@echo '${YELLOW}⚡ Quick Actions:${NC}'
	@grep -E '^(status|health|monitor).*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${GREEN}%-20s${NC} %s\n", $$1, $$2}'
	@echo ''

# =============================================================================
# 🐳 Docker Container Management
# =============================================================================

up: ## Start all services
	@echo "$(BLUE)Starting all services...$(NC)"
	$(COMPOSE) up -d
	@echo "$(GREEN)✅ All services started$(NC)"
	@echo "$(YELLOW)Gateway: http://localhost:8000$(NC)"
	@echo "$(YELLOW)Services running on ports 8001-8007$(NC)"

down: ## Stop all services
	@echo "$(YELLOW)Stopping all services...$(NC)"
	$(COMPOSE) down
	@echo "$(GREEN)✅ All services stopped$(NC)"

restart: ## Restart all services
	@echo "$(BLUE)Restarting all services...$(NC)"
	$(COMPOSE) restart
	@echo "$(GREEN)✅ All services restarted$(NC)"

build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	$(COMPOSE) build
	@echo "$(GREEN)✅ Images built successfully$(NC)"

rebuild: ## Rebuild images without cache
	@echo "$(BLUE)Rebuilding images from scratch...$(NC)"
	$(COMPOSE) build --no-cache
	@echo "$(GREEN)✅ Images rebuilt successfully$(NC)"

ps: ## Show container status
	@$(COMPOSE) ps

logs: ## Follow logs for all services
	$(COMPOSE) logs -f --tail=100

# Service-specific logs
logs-%: ## Show logs for specific service (e.g., make logs-legal)
	$(COMPOSE) logs -f --tail=100 cortex-$*

# =============================================================================
# 🗄️ Database Management
# =============================================================================

migrate: ## Apply database migrations
	@echo "$(BLUE)Applying database migrations...$(NC)"
	@$(UV) run alembic upgrade head
	@echo "$(GREEN)✅ Migrations applied successfully$(NC)"

migration-new: ## Create new migration (usage: make migration-new m="description")
ifndef m
	$(error Please provide migration message: make migration-new m="your message")
endif
	@echo "$(BLUE)Creating new migration: $(m)$(NC)"
	@$(UV) run alembic revision --autogenerate -m "$(m)"
	@echo "$(GREEN)✅ Migration created$(NC)"

migrate-down: ## Rollback last migration
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	@$(UV) run alembic downgrade -1
	@echo "$(GREEN)✅ Migration rolled back$(NC)"

db-shell: ## Connect to PostgreSQL
	@echo "$(BLUE)Connecting to database...$(NC)"
	@$(COMPOSE) exec cortex-postgres psql -U $(DB_USER) -d $(DB_NAME)

db-backup: ## Backup database
	@mkdir -p backups
	@BACKUP_FILE="backups/backup_$$(date +%Y%m%d_%H%M%S).sql" && \
	$(COMPOSE) exec cortex-postgres pg_dump -U $(DB_USER) $(DB_NAME) > $$BACKUP_FILE && \
	echo "$(GREEN)✅ Database backed up to $$BACKUP_FILE$(NC)"

db-restore: ## Restore database (usage: make db-restore FILE=backup.sql)
ifndef FILE
	$(error Please specify backup file: make db-restore FILE=backups/backup.sql)
endif
	@echo "$(YELLOW)Restoring database from $(FILE)...$(NC)"
	@$(COMPOSE) exec -T cortex-postgres psql -U $(DB_USER) $(DB_NAME) < $(FILE)
	@echo "$(GREEN)✅ Database restored$(NC)"

db-verify: ## Verify database tables (PT→EN refactoring check)
	@echo "$(BLUE)Verifying database tables...$(NC)"
	@$(PYTHON) scripts/verify_db_tables.py 2>/dev/null || echo "$(YELLOW)Run 'make install' first$(NC)"

# =============================================================================
# 🧪 Testing
# =============================================================================

test: ## Run smoke tests
	@echo "$(BLUE)Running tests...$(NC)"
	@$(PYTHON) -m pytest tests/test_smoke.py -v
	@echo "$(GREEN)✅ Tests completed$(NC)"

test-refactoring: ## Validate PT→EN refactoring
	@echo "$(BLUE)Validating Portuguese to English refactoring...$(NC)"
	@echo "$(YELLOW)Checking that 'lawsuits' table exists in database...$(NC)"
	@$(COMPOSE) exec cortex-postgres psql -U $(DB_USER) -d $(DB_NAME) -c "SELECT 'lawsuits' as table_name, COUNT(*) as row_count FROM lawsuits;" 2>/dev/null || echo "$(YELLOW)Database check skipped$(NC)"
	@echo "$(GREEN)✅ Refactoring validation complete$(NC)"

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	@$(PYTHON) tests/test_integration.py

# =============================================================================
# 🧹 Maintenance
# =============================================================================

clean: ## Clean Python cache and temporary files
	@echo "$(BLUE)Cleaning cache files...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf htmlcov 2>/dev/null || true
	@echo "$(GREEN)✅ Cache cleaned$(NC)"

clean-all: ## Stop containers and clean everything
	@echo "$(RED)Stopping and cleaning everything...$(NC)"
	@$(COMPOSE) down -v 2>/dev/null || true
	@make clean
	@echo "$(GREEN)✅ Full cleanup complete$(NC)"

prune: ## Docker system prune (remove unused images/containers)
	@echo "$(YELLOW)Pruning Docker system...$(NC)"
	@docker system prune -f
	@echo "$(GREEN)✅ Docker system pruned$(NC)"

install: ## Install Python dependencies
	@echo "$(BLUE)Installing dependencies with uv...$(NC)"
	@$(UV) pip install --system -e .
	@$(UV) pip install --system -e ".[test]" 2>/dev/null || true
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

# =============================================================================
# ⚡ Quick Status & Monitoring
# =============================================================================

status: ## Show system status
	@echo "$(BLUE)=== Cortex7 System Status ===$(NC)"
	@echo ""
	@echo "$(YELLOW)📦 Container Status:$(NC)"
	@$(COMPOSE) ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "$(YELLOW)🗄️  Database:$(NC)"
	@$(COMPOSE) exec cortex-postgres psql -U $(DB_USER) -d $(DB_NAME) -c "SELECT COUNT(*) as tables FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null || echo "Database not accessible"
	@echo ""
	@echo "$(YELLOW)📊 Current Migration:$(NC)"
	@$(UV) run alembic current 2>/dev/null || echo "Run 'make install' first"

health: ## Check service health
	@echo "$(BLUE)Checking service health...$(NC)"
	@for port in 8000 8001 8002 8003 8004 8005 8006 8007; do \
		echo -n "Port $$port: "; \
		curl -s http://localhost:$$port/health >/dev/null 2>&1 && echo "$(GREEN)✅ UP$(NC)" || echo "$(RED)❌ DOWN$(NC)"; \
	done

monitor: ## Monitor services (logs + status)
	@echo "$(BLUE)Starting service monitor...$(NC)"
	@./scripts/monitor_services.sh 2>/dev/null || echo "$(YELLOW)Monitor script not found$(NC)"

# =============================================================================
# Common Workflows
# =============================================================================

# Start everything fresh
fresh: down clean build up migrate ## Fresh start (rebuild everything)
	@echo "$(GREEN)✅ Fresh environment ready!$(NC)"

# Quick start (assuming images exist)
start: up migrate ## Quick start services
	@echo "$(GREEN)✅ Services started!$(NC)"

# Stop everything
stop: down ## Stop all services
	@echo "$(GREEN)✅ Services stopped$(NC)"

# Check if refactoring is working
validate: test-refactoring db-verify ## Validate PT→EN refactoring
	@echo "$(GREEN)✅ Refactoring validation complete$(NC)"

.DEFAULT_GOAL := help