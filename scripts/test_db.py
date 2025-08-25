#!/usr/bin/env python3
# scripts/test_db.py
from __future__ import annotations

import os
import django
from django.conf import settings
from django.db import connection

# Settings-Modul setzen (anpassen falls dein Projekt nicht "config" heißt!)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

print("DB settings:", settings.DATABASES["default"])

with connection.cursor() as cursor:
    cursor.execute("select current_database(), current_user, current_schema();")
    print("Runtime:", cursor.fetchall())
