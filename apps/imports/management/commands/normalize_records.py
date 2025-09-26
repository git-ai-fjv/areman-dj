#!/usr/bin/env python3

# apps/imports/management/commands/normalize_records.py
"""
Purpose:
    Normalize all ImportRawRecords for a given supplier where ImportRun.map_set is NULL.
    The command assigns the newest available ImportMapSet to each ImportRun and
    applies the mapping rules to populate `normalized_data`.

Usage:
    python manage.py normalize_records --supplier 70002

Behavior:
    - Finds newest ImportMapSet for the supplier + source_type of each ImportRun.
    - If no ImportMapSet exists, aborts with an error.
    - Sets ImportRun.map_set if not already set.
    - Normalizes all ImportRawRecords with `normalized_data IS NULL` in batches.
    - Logs processed counts (success vs. error).

Depends on:
    - apps.imports.models.ImportRun
    - apps.imports.models.ImportRawRecord
    - apps.imports.models.ImportMapSet / ImportMapDetail
    - apps.imports.services.mapping_engine (apply_mapping)

Example:
    python manage.py normalize_records --supplier 70002
"""

from __future__ import annotations

import logging
import traceback
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.imports.models.import_run import ImportRun
from apps.imports.models.import_raw_record import ImportRawRecord
from apps.imports.models.import_map_set import ImportMapSet
from apps.partners.models.supplier import Supplier
from apps.imports.services.mapping_engine import apply_mapping

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Normalize ImportRawRecords for a supplier where ImportRun.map_set is NULL."

    def add_arguments(self, parser):
        parser.add_argument(
            "--supplier",
            required=True,
            help="Supplier code (e.g. 70002)"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        supplier_code = options["supplier"]

        try:
            supplier = Supplier.objects.get(supplier_code=supplier_code)
        except Supplier.DoesNotExist:
            raise CommandError(f"Supplier '{supplier_code}' not found")

        runs = ImportRun.objects.filter(supplier=supplier, map_set__isnull=True)
        if not runs.exists():
            self.stdout.write(self.style.WARNING("No ImportRuns without map_set found."))
            return

        total_runs = 0
        total_success = 0
        total_errors = 0

        for run in runs:
            # find newest mapping for this supplier + source_type
            map_set = (
                ImportMapSet.objects.filter(
                    supplier=supplier,
                    source_type=run.source_type
                )
                .order_by("-valid_from")
                .first()
            )

            if not map_set:
                raise CommandError(
                    f"No ImportMapSet found for supplier={supplier_code}, source_type={run.source_type.code}"
                )

            run.map_set = map_set
            run.save(update_fields=["map_set"])

            # process raw records
            raw_records = ImportRawRecord.objects.filter(
                import_run=run, normalized_data__isnull=True
            )

            batch_size = 1000
            buffer = []
            success_count = 0
            error_count = 0

            for rec in raw_records.iterator():
                try:
                    rec.normalized_data = apply_mapping(rec.payload, map_set)
                    rec.error_message_product_import = None
                    success_count += 1
                except Exception as e:
                    tb = traceback.format_exc()
                    logger.error(
                        f"Normalization failed for ImportRawRecord {rec.id}: {e}\n{tb}"
                    )
                    rec.error_message_product_import = f"Normalization error: {e}"
                    error_count += 1
                buffer.append(rec)

                if len(buffer) >= batch_size:
                    ImportRawRecord.objects.bulk_update(
                        buffer, ["normalized_data", "error_message_product_import"]
                    )
                    buffer.clear()

            if buffer:
                ImportRawRecord.objects.bulk_update(
                    buffer, ["normalized_data", "error_message_product_import"]
                )

            total_runs += 1
            total_success += success_count
            total_errors += error_count

            self.stdout.write(self.style.SUCCESS(
                f"Processed ImportRun {run.id}: {success_count} success, {error_count} errors "
                f"with map_set {map_set.id}."
            ))

        self.stdout.write(self.style.SUCCESS(
            f"Done. {total_runs} runs processed, {total_success} records normalized, {total_errors} errors."
        ))
