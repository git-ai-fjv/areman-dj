# apps/imports/management/commands/seed_import_transform_types.py

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


