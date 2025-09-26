#!/usr/bin/env python3

# apps/imports/management/commands/seed_import_source_types.py
"""
Purpose:
    Management command to seed default `ImportSourceType` records. Ensures
    consistent source type classification for imports (file, API, manual, other).

Context:
    Part of the `apps.imports` app. Used during system setup or migrations
    to initialize baseline source type records.

Used by:
    - Developers and operators via `python manage.py seed_import_source_types`
    - Import commands that require a valid ImportSourceType reference
      (e.g., `import_komatsu`, `import_elsaesser`)

Depends on:
    - apps.imports.models.import_source_type.ImportSourceType
    - Django management command framework

Example:
    # Seed all default import source types
    python manage.py seed_import_source_types
"""


from __future__ import annotations

from django.core.management.base import BaseCommand
from django.apps import apps


class Command(BaseCommand):
    help = "Seed default ImportSourceType records (idempotent)."

    DEFAULTS = [
        ("file", "Flat file import (CSV, XLSX, etc.)"),
        ("api", "API-based import"),
        ("manual", "Manual user input"),
        ("other", "Other or unspecified source"),
    ]

    def handle(self, *args, **options):
        ImportSourceType = apps.get_model("imports", "ImportSourceType")

        for code, desc in self.DEFAULTS:
            obj, created = ImportSourceType.objects.get_or_create(
                code=code, defaults={"description": desc}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created: {code}"))
            else:
                self.stdout.write(f"Exists: {code}")
