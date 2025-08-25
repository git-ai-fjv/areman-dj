# scripts/bootstrap_django.py
### prepare django environment for standalone scripts
### use: python scripts/bootstrap_django.py
# # 🔌 Bootstrap Django environment
# import scripts.bootstrap_django  # noqa: F401


import os
import django
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

