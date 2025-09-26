#!/usr/bin/env python3

# apps/imports/management/commands/import_komatsu.py
"""
Purpose:
    Management command to import Komatsu product data from Excel files into
    `ImportRun` and `ImportRawRecord`. Supports both automatic detection of
    the newest file and explicit file path overrides.

Context:
    Part of the `apps.imports` app. Runs as a Django management command.
    Used to bring supplier Excel catalogs into the import pipeline, with
    validation and dry-run support.

Used by:
    - Developers (manual execution via `python manage.py import_komatsu`)
    - Automated import jobs (scheduled data ingestion)
    - Downstream processing tasks that consume `ImportRun` and `ImportRawRecord`

Depends on:
    - pandas (Excel parsing)
    - apps.imports.models.ImportRun (import session tracking)
    - apps.imports.models.ImportRawRecord (raw Excel rows storage)
    - apps.imports.models.ImportSourceType (to classify source type)
    - apps.partners.models.Supplier (supplier reference)
    - Django transaction management and logging

Example:
    # Auto-detect newest file and import
    python manage.py import_komatsu --supplier SUPP01

    # Dry run (preview up to 20 rows, no DB changes)
    python manage.py import_komatsu --supplier SUPP01 --dry-run

    # Import specific file
    python manage.py import_komatsu --supplier SUPP01 --file apps/imports/data/SUPP01/2025/08/komatsu_06-25.xlsx
"""



from __future__ import annotations

import logging
import traceback
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
    Import the latest Komatsu Excel file into ImportRun + ImportRawRecord.
    """

    help = """Import the newest Komatsu Excel file for a supplier into ImportRawRecord.

Usage:
  python manage.py import_komatsu --supplier SUPP01 [--file path/to/file.xlsx] [--dry-run]

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
            help="Parse and validate, but do not write to the database.",
        )

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

    def _is_valid_row(self, row_dict: dict) -> bool:
        """A row is valid only if Part Number and Description/Beschreibung are present."""
        part_number = str(row_dict.get("Part Number", "") or "").strip()
        description = (
            str(row_dict.get("Description", "") or row_dict.get("Beschreibung", "") or "").strip()
        )
        return bool(part_number and description)

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        supplier_code: str = options["supplier"]
        file_override: str = options["file"]
        dry_run: bool = options["dry_run"]

        try:
            try:
                supplier = Supplier.objects.get(supplier_code=supplier_code)
            except Supplier.DoesNotExist:
                raise CommandError(f"Supplier '{supplier_code}' not found")

            try:
                source_type = ImportSourceType.objects.get(code="file")
            except ImportSourceType.DoesNotExist:
                raise CommandError("ImportSourceType 'file' not found")

            if file_override:
                file_path = Path(file_override)
                if not file_path.exists():
                    raise CommandError(f"File not found: {file_path}")
            else:
                file_path = self._find_latest_file(supplier_code)

            self.stdout.write(f"Using file: {file_path}")

            df = pd.read_excel(file_path)
            total = len(df)
            self.stdout.write(f"Found {total} rows in Excel.")

            # ---------------- DRY-RUN ----------------
            if dry_run:
                self.stdout.write(self.style.WARNING("[DRY-RUN] No DB changes."))

                max_preview = 20
                preview_rows = []
                skipped = 0
                valid = 0

                for i, row in df.iterrows():
                    row_dict = row.to_dict()
                    if not self._is_valid_row(row_dict):
                        skipped += 1
                        continue
                    if len(preview_rows) < max_preview:
                        preview_rows.append((i + 1, row_dict))
                    valid += 1
                    if len(preview_rows) >= max_preview:
                        break

                for line_no, row_dict in preview_rows:
                    self.stdout.write(f"Line {line_no}: {row_dict}")

                if valid > max_preview:
                    self.stdout.write(
                        f"... skipped displaying {valid - max_preview} rows "
                        f"(showing first {max_preview})"
                    )

                self.stdout.write(
                    f"Total rows = {total}, skipped invalid = {skipped}, valid = {valid}"
                )
                return

            # ---------------- REAL IMPORT ----------------
            run = ImportRun.objects.create(
                supplier=supplier,
                source_type=source_type,
                source_file=str(file_path),
                started_at=timezone.now(),
                status="running",
            )

            batch_size = 5000
            buffer: list[ImportRawRecord] = []
            skipped = 0
            inserted = 0

            for i, row in df.iterrows():
                row_dict = row.to_dict()
                if not self._is_valid_row(row_dict):
                    skipped += 1
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
                    self.stdout.write(f"Inserted {inserted} rows...")

            if buffer:
                ImportRawRecord.objects.bulk_create(buffer, batch_size)
                inserted += len(buffer)

            run.finished_at = timezone.now()
            run.total_records = inserted
            run.status = "success"
            run.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f"ImportRun {run.id} complete — {inserted} rows imported "
                    f"(skipped {skipped} invalid rows, batch size {batch_size})."
                )
            )

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Komatsu import failed: {e}")
            raise CommandError(f"Error during import: {e}\n{tb}")


#
# Auto-neueste Datei finden:
#   python manage.py import_komatsu --supplier SUPP01
#
# Trockenlauf (nur anzeigen, max 20 Zeilen, Pflichtfelder Part Number + Description):
#   python manage.py import_komatsu --supplier SUPP01 --dry-run
#
# Spezifische Datei importieren:
#   python manage.py import_komatsu --supplier SUPP01 --file apps/imports/data/SUPP01/2025/08/komatsu_06-25.xlsx

