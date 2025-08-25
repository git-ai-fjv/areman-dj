# scripts/bootstrap_django.py
# Created according to the user's Copilot Base Instructions.
"""
🔌 Bootstrap Django environment for standalone scripts.

Usage:
    import scripts.bootstrap_django  # noqa: F401
"""

import sys
import os
from pathlib import Path

import django
from dotenv import load_dotenv

# --- Ensure project root is in PYTHONPATH ---
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# --- Load .env file if present ---
load_dotenv()

# --- Setup Django ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")  # ggf. anpassen
django.setup()
