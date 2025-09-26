#!/usr/bin/env python3

# apps/imports/management/commands/universal_excel_importer.py
"""
Purpose:
    Generic Excel importer that loads spreadsheet rows into ImportRawRecord.
    Performs no field mapping — it only stores cleaned raw rows as JSON for later
    supplier-specific transformation.

Context:
    Part of the `apps.imports` app. Used to handle bulk uploads of supplier Excel files
    and to initialize raw import runs in a standardized way.

Used by:
    - Operators via `python manage.py universal_excel_importer`
    - Downstream import pipeline services that map raw records to business objects

Depends on:
    - apps.imports.models.import_run.ImportRun
    - apps.imports.models.import_raw_record.ImportRawRecord
    - apps.imports.models.import_source_type.ImportSourceType
    - apps.partners.models.supplier.Supplier
    - pandas for reading Excel files

Example:
    # Preview 20 rows without persisting them
    python manage.py universal_excel_importer --supplier SUPP01 --dry-run

    # Import the latest Excel file for a supplier
    python manage.py universal_excel_importer --supplier SUPP01
"""


from __future__ import annotations

import logging
import math
import traceback
import time
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.imports.models.import_run import ImportRun
from apps.imports.models.import_raw_record import ImportRawRecord
from apps.imports.models.import_source_type import ImportSourceType

from apps.partners.models.supplier import Supplier

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Universal Excel importer: loads Excel rows into ImportRawRecord
    without field mapping (supplier-specific mapping is applied later).
    """

    help = """Universal Excel importer: stores raw Excel rows as JSON.

Usage:
  python manage.py universal_excel_importer --supplier SUPP01 [--file path/to/file.xlsx] [--dry-run]

By default, the command looks in:
  apps/imports/data/<SUPPLIER>/<YYYY>/<MM>/ for the newest file.
"""

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--supplier", required=True, help="Supplier code (e.g., SUPP01)"
        )
        parser.add_argument(
            "--file",
            default="",
            help="Optional override: explicit file path to import",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and preview (max 20 rows), but do not write to the database.",
        )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _find_latest_file(self, supplier: str) -> Path:
        base_dir = Path("apps/imports/data") / supplier
        if not base_dir.exists():
            raise CommandError(f"Data directory not found: {base_dir}")

        years = [d for d in base_dir.iterdir() if d.is_dir() and d.name.isdigit()]
        if not years:
            raise CommandError(f"No year directories in {base_dir}")
        latest_year = max(years, key=lambda d: d.name)

        months = [d for d in latest_year.iterdir() if d.is_dir() and d.name.isdigit()]
        if not months:
            raise CommandError(f"No month directories in {latest_year}")
        latest_month = max(months, key=lambda d: d.name)

        files = list(latest_month.glob("*.xlsx"))
        if not files:
            raise CommandError(f"No Excel files found in {latest_month}")
        latest_file = max(files, key=lambda f: f.stat().st_mtime)

        return latest_file

    def _clean_row_dict(self, row_dict: dict) -> dict:
        """Replace NaN/inf with None so JSON is valid for Postgres."""
        cleaned = {}
        for k, v in row_dict.items():
            if v is None:
                cleaned[k] = None
            elif isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                cleaned[k] = None
            else:
                cleaned[k] = v
        return cleaned

    def _is_effectively_empty(self, row_dict: dict) -> bool:
        """Return True if a row is effectively empty (only NaN/None/""/0.0)."""
        for v in row_dict.values():
            if v is None or v == "" or (isinstance(v, float) and math.isnan(v)):
                continue
            if isinstance(v, (int, float)) and v == 0:
                continue
            return False
        return True

    # ------------------------------------------------------------------ #
    # Main
    # ------------------------------------------------------------------ #

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        supplier_code: str = options["supplier"]
        file_override: str = options["file"]
        dry_run: bool = options["dry_run"]

        def log_step(step_name: str, last_time: float) -> float:
            """Log elapsed seconds since last step and return new timestamp."""
            now = time.time()
            elapsed = now - last_time
            self.stdout.write(self.style.NOTICE(f"[Timing] {step_name}: {elapsed:.2f}s"))
            return now

        try:
            t0 = time.time()

            # Supplier
            try:
                supplier = Supplier.objects.get(supplier_code=supplier_code)
            except Supplier.DoesNotExist:
                raise CommandError(f"Supplier '{supplier_code}' not found")
            t0 = log_step("Loaded Supplier", t0)

            # Source type (always "file")
            try:
                source_type = ImportSourceType.objects.get(code="file")
            except ImportSourceType.DoesNotExist:
                raise CommandError("ImportSourceType 'file' not found")
            t0 = log_step("Loaded ImportSourceType", t0)

            # File
            if file_override:
                file_path = Path(file_override)
                if not file_path.exists():
                    raise CommandError(f"File not found: {file_path}")
            else:
                file_path = self._find_latest_file(supplier_code)

            self.stdout.write(f"Using file: {file_path}")
            t0 = log_step("Resolved file path", t0)

            # Read Excel
            df = pd.read_excel(file_path)
            total = len(df)
            self.stdout.write(f"Found {total} rows in Excel.")
            t0 = log_step("Read Excel file", t0)

            if dry_run:
                self.stdout.write(self.style.WARNING("[DRY-RUN] Preview only."))
                for i, row in df.head(20).iterrows():
                    row_dict = self._clean_row_dict(row.to_dict())
                    if self._is_effectively_empty(row_dict):
                        continue
                    self.stdout.write(f"Line {i+1}: {row_dict}")
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[DRY-RUN] Showing first 20 of {total} rows. No DB changes."
                    )
                )
                return

            # Create ImportRun
            run = ImportRun.objects.create(
                supplier=supplier,
                source_type=source_type,
                source_file=str(file_path),
                started_at=timezone.now(),
                status="running",
            )
            t0 = log_step("Created ImportRun", t0)

            buffer: list[ImportRawRecord] = []
            batch_size = 5000
            inserted = 0

            for i, row in df.iterrows():
                row_dict = self._clean_row_dict(row.to_dict())

                # Skip empty or pseudo-empty rows
                if self._is_effectively_empty(row_dict):
                    continue

                buffer.append(
                    ImportRawRecord(
                        import_run=run,
                        line_number=i + 1,
                        payload=row_dict,
                    )
                )

                if len(buffer) >= batch_size:
                    ImportRawRecord.objects.bulk_create(buffer, batch_size)
                    inserted += len(buffer)
                    buffer.clear()

            if buffer:
                ImportRawRecord.objects.bulk_create(buffer, batch_size)
                inserted += len(buffer)
            t0 = log_step(f"Inserted {inserted} records", t0)

            # Finalize run
            run.finished_at = timezone.now()
            run.total_records = inserted
            run.status = "success"
            run.save()
            t0 = log_step("Finalized ImportRun", t0)

            self.stdout.write(
                self.style.SUCCESS(
                    f"ImportRun {run.id} complete — {inserted} rows imported."
                )
            )

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Universal Excel import failed: {e}")
            raise CommandError(f"Error during import: {e}\n{tb}")


#
# Examples:
#
# Auto-neueste Datei finden und importieren:
#   python manage.py universal_excel_importer --supplier SUPP01
#
# Dry-Run (nur Vorschau von 20 Zeilen):
#   python manage.py universal_excel_importer --supplier SUPP01 --dry-run
#
# Spezifische Datei importieren:
#   python manage.py universal_excel_importer --supplier SUPP01 --file apps/imports/data/SUPP01/2025/08/test.xlsx
#
# Beispielausgabe mit Zeitmessung und Filter:
#   Using file: apps/imports/data/SUPP01/2025/08/test.xlsx
#   Found 1048575 rows in Excel.
#   [Timing] Loaded Supplier: 0.00s
#   [Timing] Loaded ImportSourceType: 0.00s
#   [Timing] Resolved file path: 0.00s
#   [Timing] Read Excel file: 46.51s
#   [Timing] Created ImportRun: 0.00s
#   [Timing] Inserted 20 records: 0.03s
#   [Timing] Finalized ImportRun: 0.00s
#   ImportRun 3 complete — 20 rows imported.


