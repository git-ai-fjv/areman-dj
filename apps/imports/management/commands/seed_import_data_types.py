#!/usr/bin/env python3
# apps/imports/management/commands/seed_import_data_types.py
"""
Purpose:
    Management command to seed default data types (str, int, decimal, bool, date, datetime)
    into the `ImportDataType` table. Ensures the system has the required baseline
    for describing import field types.

Context:
    Part of the `apps.imports` app. Used during initial setup or migrations
    to populate the database with standard import data types.

Used by:
    - Developers (manual execution via `python manage.py seed_import_data_types`)
    - Initial project setup scripts
    - Any process that relies on consistent `ImportDataType` definitions

Depends on:
    - apps.imports.models.import_data_type.ImportDataType
    - Django management command framework

Example:
    # Seed default data types
    python manage.py seed_import_data_types
"""


from __future__ import annotations

from django.core.management.base import BaseCommand
from apps.imports.models.import_data_type import ImportDataType


class Command(BaseCommand):
    """
    Seed basic datatypes into ImportDataType (str, int, decimal, bool).
    """

    help = "Seed ImportDataType with default values (idempotent)."

    DEFAULT_TYPES = [
        ("str", "String"),
        ("int", "Integer"),
        ("decimal", "Decimal number"),
        ("bool", "Boolean"),
        ("date", "Date"),
        ("datetime", "Date and time"),
    ]

    def handle(self, *args, **options) -> None:
        created_count = 0
        for code, desc in self.DEFAULT_TYPES:
            obj, created = ImportDataType.objects.get_or_create(
                code=code,
                defaults={"description": desc},
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created ImportDataType: {code}"))
            else:
                self.stdout.write(f"Exists: {code}")

        self.stdout.write(
            self.style.SUCCESS(f"Seeding complete. {created_count} new datatypes added.")
        )


