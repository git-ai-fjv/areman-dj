## 🚀 Makefile Cheatsheet

Mit `make` oder `make help` bekommst du dieses Menü im Terminal.

### 🔵 Daily Business
```bash
make migrate          # Apply database migrations
make makemigrations   # Create new migrations based on models
make run              # Start Django development server
```

### 🟦 Hilfreiche Tools
```bash
make lint             # Run flake8 checks
make format           # Auto-format code (black)
make isort            # Sort imports
```

### 🌱 Stammdaten-Seeds
```bash
make seed             # Run base-data seeding script
```

### 🔴 Gefährlich – Datenverlust!
```bash
make deletedb         # ⚠ DROP database (DATA LOSS!)
make resetdb          # ⚠ RESET database (ALL data will be lost!)
```

### 🛠️ Sonstiges
```bash
make reset-app APP=myapp   # Reset migrations for a single app
make clear-migrations      # Delete ALL migration files (DANGEROUS!)
make shell                 # Open Django shell
make superuser             # Create superuser interactively
make check                 # Django system checks
```
