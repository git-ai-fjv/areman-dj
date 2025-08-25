#!/usr/bin/env bash
set -euo pipefail

# Root-Verzeichnis ermitteln
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Cleaning all Django migration files under $ROOT_DIR/apps ..."

# Finde und lösche alle Dateien, die mit 0xxx_ anfangen (außer __init__.py)
find "$ROOT_DIR/apps" -type f -path "*/migrations/[0-9][0-9][0-9][0-9]_*.py" -print -delete

# Sicherheit: alle zugehörigen .pyc Dateien auch killen
find "$ROOT_DIR/apps" -type f -path "*/migrations/*.pyc" -print -delete

echo "All migration files removed."

