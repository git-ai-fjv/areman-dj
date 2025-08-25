#!/usr/bin/env python3
# apps/imports/management/commands/seed_import_source_types.py
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
