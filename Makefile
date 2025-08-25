# Makefile for Django project
# Default target: show help
.DEFAULT_GOAL := help

# -----------------------------------------------------------------------------
# Utility
# -----------------------------------------------------------------------------

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

# -----------------------------------------------------------------------------
# Database & migrations
# -----------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------
# Django management
# -----------------------------------------------------------------------------

run:  ## Run the Django development server
	python manage.py runserver

shell:  ## Open Django shell
	python manage.py shell

superuser:  ## Create a Django superuser
	python manage.py createsuperuser

check:  ## Run Django system checks
	python manage.py check

# -----------------------------------------------------------------------------
# Quality
# -----------------------------------------------------------------------------

lint:  ## Run flake8 lint checks
	flake8 apps

format:  ## Auto-format code with black
	black apps

isort:  ## Sort imports with isort
	isort apps

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

test:  ## Run tests with pytest
	pytest -q --disable-warnings

coverage:  ## Run tests with coverage
	pytest --cov=apps --cov-report=term-missing

deletedb:
	@echo "Deleting database..."
	python scripts/dbutils.py delete

createdb:
	@echo "Creating database..."
	python scripts/dbutils.py create

resetdb: deletedb createdb migrate
	@echo "Database reset complete."

