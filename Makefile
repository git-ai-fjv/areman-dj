# Makefile for Django project
.DEFAULT_GOAL := help

# Colors
CYAN  := \033[36m
BLUE  := \033[34m
RED   := \033[31m
GREEN := \033[32m
BOLD  := \033[1m
RESET := \033[0m

DOCS_DIR := docs
DOCS_FILE := $(DOCS_DIR)/MAKE_CMDS.md

# =============================================================================
# Help
# =============================================================================
help: gen-docs  ## Show this help (and regenerate docs/MAKE_CMDS.md)
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
	@echo "📄 Updated documentation: $(DOCS_FILE)"

# =============================================================================
# Docs
# =============================================================================
gen-docs:
	@mkdir -p $(DOCS_DIR)
	@echo "## 🚀 Makefile Cheatsheet" > $(DOCS_FILE)
	@echo "" >> $(DOCS_FILE)
	@echo "Mit \`make\` oder \`make help\` bekommst du dieses Menü im Terminal." >> $(DOCS_FILE)
	@echo "" >> $(DOCS_FILE)

	@echo "### 🔵 Daily Business" >> $(DOCS_FILE)
	@echo "\`\`\`bash" >> $(DOCS_FILE)
	@echo "make migrate          # Apply database migrations" >> $(DOCS_FILE)
	@echo "make makemigrations   # Create new migrations based on models" >> $(DOCS_FILE)
	@echo "make run              # Start Django development server" >> $(DOCS_FILE)
	@echo "\`\`\`" >> $(DOCS_FILE)
	@echo "" >> $(DOCS_FILE)

	@echo "### 🟦 Hilfreiche Tools" >> $(DOCS_FILE)
	@echo "\`\`\`bash" >> $(DOCS_FILE)
	@echo "make lint             # Run flake8 checks" >> $(DOCS_FILE)
	@echo "make format           # Auto-format code (black)" >> $(DOCS_FILE)
	@echo "make isort            # Sort imports" >> $(DOCS_FILE)
	@echo "\`\`\`" >> $(DOCS_FILE)
	@echo "" >> $(DOCS_FILE)

	@echo "### 🌱 Stammdaten-Seeds" >> $(DOCS_FILE)
	@echo "\`\`\`bash" >> $(DOCS_FILE)
	@echo "make seed             # Run base-data seeding script" >> $(DOCS_FILE)
	@echo "\`\`\`" >> $(DOCS_FILE)
	@echo "" >> $(DOCS_FILE)

	@echo "### 🔴 Gefährlich – Datenverlust!" >> $(DOCS_FILE)
	@echo "\`\`\`bash" >> $(DOCS_FILE)
	@echo "make deletedb         # ⚠ DROP database (DATA LOSS!)" >> $(DOCS_FILE)
	@echo "make resetdb          # ⚠ RESET database (ALL data will be lost!)" >> $(DOCS_FILE)
	@echo "\`\`\`" >> $(DOCS_FILE)
	@echo "" >> $(DOCS_FILE)

	@echo "### 🛠️ Sonstiges" >> $(DOCS_FILE)
	@echo "\`\`\`bash" >> $(DOCS_FILE)
	@echo "make reset-app APP=myapp   # Reset migrations for a single app" >> $(DOCS_FILE)
	@echo "make clear-migrations      # Delete ALL migration files (DANGEROUS!)" >> $(DOCS_FILE)
	@echo "make shell                 # Open Django shell" >> $(DOCS_FILE)
	@echo "make superuser             # Create superuser interactively" >> $(DOCS_FILE)
	@echo "make check                 # Django system checks" >> $(DOCS_FILE)
	@echo "\`\`\`" >> $(DOCS_FILE)
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
	$(MAKE) clear-migrations
	$(MAKE) makemigrations
	$(MAKE) migrate
	$(MAKE) seed
	@echo ""
	@echo "─────────────────────────────"
	@echo "$(BOLD) Database reset complete ✅$(RESET)"
	@echo "─────────────────────────────"
	@echo "$(GREEN)✔ Database created$(RESET)"
	@echo "$(GREEN)✔ Migrations deleted$(RESET)"
	@echo "$(GREEN)✔ new Migrations applied$(RESET)"
	@echo "$(GREEN)✔ Base data seeded$(RESET)"
	@echo "$(GREEN)✔ Default supplier created$(RESET)"
	@echo "$(GREEN)✔ Superuser ready (fjv)$(RESET)"
	@echo "─────────────────────────────"

# =============================================================================
# Django management
# =============================================================================
run:  ## Run the Django development server
	python manage.py runserver 0.0.0.0:8005

shell:  ## Open Django shell
	python manage.py shell

superuser:  ## Create a Django superuser interactively
	python manage.py createsuperuser

check:  ## Run Django system checks
	python manage.py check

# =============================================================================
# Project Collector
# =============================================================================
collect:  ## Collect all relevant source files into one combined file (ignores .gitignore and migrations)
	@echo "Collecting project files..."
	@git ls-files \
		| grep -Ei '\.py$$|\.md$$|\.txt$$|dockerfile|makefile' \
		| grep -Ev '/migrations/' \
		| xargs awk 'FNR==1{print "\n\n# FILE:",FILENAME,"\n"}{print}' \
		> all_project_combined.txt
	@echo ""
	@echo "$(GREEN)✔ Combined file written to all_project_combined.txt$(RESET)"
