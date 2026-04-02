.PHONY: help dev dev-up dev-down migrate test lint format check build clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ==================== Development ====================

dev: ## Start all services in development mode
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d

dev-up: ## Start infrastructure only (PostgreSQL, Redis, MinIO, RabbitMQ)
	docker compose up -d postgres redis minio rabbitmq

dev-down: ## Stop all services
	docker compose down

dev-logs: ## Tail all service logs
	docker compose logs -f

# ==================== Backend ====================

backend-install: ## Install backend Python dependencies
	cd backend && pip install -r requirements.txt -r requirements-dev.txt

backend-run: ## Run backend server locally
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-migrate: ## Run database migrations
	cd backend && alembic upgrade head

backend-migrate-create: ## Create a new migration (usage: make migrate-create msg="description")
	cd backend && alembic revision --autogenerate -m "$(msg)"

backend-migrate-downgrade: ## Rollback last migration
	cd backend && alembic downgrade -1

backend-seed: ## Seed mock data
	cd backend && python scripts/seed_data.py

# ==================== Agent ====================

agent-run: ## Run Agent service locally
	cd agent && uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# ==================== Scraper ====================

scraper-run: ## Run 1688 spider
	cd scraper && scrapy crawl alibaba

scraper-list: ## List available spiders
	cd scraper && scrapy list

# ==================== Frontend ====================

frontend-install: ## Install frontend dependencies
	cd frontend && npm install

frontend-run: ## Run frontend dev server
	cd frontend && npm run dev

frontend-build: ## Build frontend for production
	cd frontend && npm run build

# ==================== Testing ====================

test: ## Run all tests
	cd backend && pytest tests/ -v --tb=short

test-cov: ## Run tests with coverage report
	cd backend && pytest tests/ -v --cov=app --cov-report=html --cov-report=term

test-integration: ## Run integration tests only
	cd backend && pytest tests/ -v -m integration

# ==================== Code Quality ====================

lint: ## Run all linters
	cd backend && flake8 app/ tests/ && mypy app/
	cd frontend && npm run lint

format: ## Auto-format code
	cd backend && black app/ tests/ && isort app/ tests/
	cd frontend && npm run format

check: ## Run format check (no changes)
	cd backend && black --check app/ tests/ && isort --check-only app/ tests/

# ==================== Docker ====================

build: ## Build all Docker images
	docker compose build

# ==================== Cleanup ====================

clean: ## Remove all generated files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf backend/htmlcov/ backend/.pytest_cache/
	rm -rf frontend/dist/
