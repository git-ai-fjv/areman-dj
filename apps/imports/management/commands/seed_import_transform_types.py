# apps/imports/management/commands/seed_import_transform_types.py
"""
Purpose:
    Management command to seed the `ImportTransformType` table with
    predefined transformation types (e.g., uppercase, lowercase, int, decimal).
    Ensures that import pipelines have a consistent set of transform functions.

Context:
    Part of the `apps.imports` app. Used during setup or migrations
    to initialize transformation options for import processing.

Used by:
    - Developers and operators via `python manage.py seed_import_transform_types`
    - Import pipeline services that apply transformation rules on raw values

Depends on:
    - apps.imports.models.import_transform_type.ImportTransformType
    - Django management command framework

Example:
    # Seed all default transform types
    python manage.py seed_import_transform_types
"""


from __future__ import annotations
from django.core.management.base import BaseCommand
from apps.imports.models.import_transform_type import ImportTransformType


TRANSFORM_TYPES = [
    ("uppercase", "Convert string to UPPERCASE"),
    ("lowercase", "Convert string to lowercase"),
    ("strip", "Trim whitespace"),
    ("int", "Convert value to integer"),
    ("decimal", "Convert value to Decimal"),
    ("bool", "Convert value to Boolean"),
]


class Command(BaseCommand):
    help = "Seed ImportTransformType table with predefined transform types."

    def handle(self, *args, **options) -> None:
        created_count = 0
        for code, desc in TRANSFORM_TYPES:
            obj, created = ImportTransformType.objects.get_or_create(
                code=code,
                defaults={"description": desc},
            )
            if created:
                created_count += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created_count} ImportTransformTypes (total {ImportTransformType.objects.count()})"
            )
        )


