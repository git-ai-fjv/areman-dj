#!/usr/bin/env python3
# apps/imports/management/commands/clear_supplier_imports.py

"""
Purpose:
    Management command to delete all ImportRun and ImportRawRecord entries
    for a given supplier. This effectively clears all import history and raw
    records for that supplier.

Context:
    Belongs to the imports app. Useful for cleanup, re-import testing, or
    removing bad imports.

Used by:
    - Developers (manual execution via manage.py)
    - Admin/ops scripts for resetting supplier imports

Depends on:
    - apps.imports.models.ImportRun
    - apps.imports.models.ImportRawRecord
    - apps.partners.models.Supplier

Example:
    # Delete all Komatsu (70002) imports
    python manage.py clear_supplier_imports --supplier 70002

    # Dry-run only (show counts, do not delete)
    python manage.py clear_supplier_imports --supplier 70002 --dry-run
"""

from __future__ import annotations

import logging
import traceback
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.imports.models.import_run import ImportRun
from apps.imports.models.import_raw_record import ImportRawRecord
from apps.partners.models.supplier import Supplier

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Delete all ImportRun and ImportRawRecord entries for a given supplier.
    """

    help = "Delete all ImportRun and ImportRawRecord entries for a given supplier."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--supplier",
            required=True,
            help="Supplier code (e.g., 70002, SUPP01).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted, but do not delete anything.",
        )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        supplier_code: str = options["supplier"]
        dry_run: bool = options["dry_run"]

        try:
            try:
                supplier = Supplier.objects.get(supplier_code=supplier_code)
            except Supplier.DoesNotExist:
                raise CommandError(f"Supplier '{supplier_code}' not found.")

            runs = ImportRun.objects.filter(supplier=supplier)
            run_count = runs.count()
            raw_count = ImportRawRecord.objects.filter(import_run__supplier=supplier).count()

            if dry_run:
                self.stdout.write(self.style.WARNING("[DRY-RUN] No DB changes."))
                self.stdout.write(
                    f"Supplier {supplier_code}: would delete {run_count} ImportRuns "
                    f"and {raw_count} ImportRawRecords."
                )
                return

            # Delete raw records first (they are FK children of ImportRun)
            ImportRawRecord.objects.filter(import_run__supplier=supplier).delete()
            runs.delete()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Deleted {run_count} ImportRuns and {raw_count} ImportRawRecords "
                    f"for supplier {supplier_code}."
                )
            )

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Failed to clear supplier imports: {e}")
            raise CommandError(f"Error during deletion: {e}\n{tb}")
