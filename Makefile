# Makefile for Django project
.DEFAULT_GOAL := help

# Colors
CYAN  := \033[36m
BLUE  := \033[34m
RED   := \033[31m
BOLD  := \033[1m
RESET := \033[0m

# =============================================================================
# Help
# =============================================================================
help:  ## Show this help (grouped by section)
	@echo ""
	@echo "$(BOLD)Most common targets:$(RESET)"
	@echo "  $(BLUE)migrate$(RESET)            Apply database migrations"
	@echo "  $(BLUE)makemigrations$(RESET)     Create new migrations based on models"
	@echo "  $(BLUE)run$(RESET)                Run the Django development server"
	@echo "  $(RED)resetdb$(RESET)             ⚠ RESET DB (ALL DATA WILL BE LOST!)"
	@echo "  $(CYAN)test$(RESET)               Run all tests"
	@echo ""
	@echo "$(BOLD)Quality$(RESET)"
	@echo "  $(CYAN)lint$(RESET)               Run flake8 lint checks"
	@echo "  $(CYAN)format$(RESET)             Auto-format code with black"
	@echo "  $(CYAN)isort$(RESET)              Sort imports with isort"
	@echo ""
	@echo "$(BOLD)Tests$(RESET)"
	@echo "  $(CYAN)test$(RESET)               Run tests with pytest"
	@echo "  $(CYAN)coverage$(RESET)           Run tests with coverage"
	@echo ""
	@echo "$(BOLD)Seeds$(RESET)"
	@echo "  $(CYAN)seed$(RESET)               Seed base data (organizations, manufacturers, etc.)"
	@echo ""
	@echo "$(BOLD)Database & migrations$(RESET)"
	@echo "  $(CYAN)reset-app$(RESET)          Reset a single app (APP=appname)"
	@echo "  $(CYAN)clear-migrations$(RESET)   Delete all migration files (DANGEROUS!)"
	@echo "  $(RED)deletedb$(RESET)            ⚠ DROP the database (DATA LOSS!)"
	@echo "  $(CYAN)createdb$(RESET)           Create the database (Postgres/SQLite)"
	@echo "  $(RED)resetdb$(RESET)             ⚠ RESET the database (ALL data will be lost!)"
	@echo "  $(BLUE)migrate$(RESET)            Apply database migrations"
	@echo "  $(BLUE)makemigrations$(RESET)     Create new migrations based on models"
	@echo ""
	@echo "$(BOLD)Django management$(RESET)"
	@echo "  $(BLUE)run$(RESET)                Run the Django development server"
	@echo "  $(CYAN)shell$(RESET)              Open Django shell"
	@echo "  $(CYAN)superuser$(RESET)          Create a Django superuser interactively"
	@echo "  $(CYAN)check$(RESET)              Run Django system checks"
	@echo ""

# =============================================================================
# Quality
# =============================================================================

lint:  ## Run flake8 lint checks
	flake8 apps

format:  ## Auto-format code with black
	black apps

isort:  ## Sort imports with isort
	isort apps

# =============================================================================
# Tests
# =============================================================================

test:  ## Run tests with pytest
	pytest -q --disable-warnings

coverage:  ## Run tests with coverage
	pytest --cov=apps --cov-report=term-missing

# =============================================================================
# Seeds
# =============================================================================

seed:  ## Seed base data (organizations, manufacturers, etc.)
	@echo "Seeding base data..."
	bash scripts/seed_base_data.sh
	@echo "Seeding complete."

# =============================================================================
# Database & migrations
# =============================================================================

migrate:  ## Apply database migrations
	python manage.py migrate

makemigrations:  ## Create new migrations based on models
	python manage.py makemigrations

reset-app:  ## Reset a single app (APP=appname)
	rm -f apps/$(APP)/migrations/0*.py
	python manage.py migrate $(APP) zero || true
	python manage.py makemigrations $(APP)
	python manage.py migrate $(APP)

clear-migrations:  ## Delete all migration files (DANGEROUS!)
	find apps -type f -path "*/migrations/0*.py" -delete

deletedb:  ## Drop the database (Postgres/SQLite)
	@echo "Deleting database..."
	python scripts/dbutils.py delete

createdb:  ## Create the database (Postgres/SQLite)
	@echo "Creating database..."
	python scripts/dbutils.py create

resetdb:  ## Reset database (drop, create, migrate, seed)
	$(MAKE) deletedb
	$(MAKE) createdb
	$(MAKE) migrate
	$(MAKE) seed
	@echo "Database reset complete."

# =============================================================================
# Django management
# =============================================================================

run:  ## Run the Django development server
	python manage.py runserver

shell:  ## Open Django shell
	python manage.py shell

superuser:  ## Create a Django superuser interactively
	python manage.py createsuperuser

check:  ## Run Django system checks
	python manage.py check
