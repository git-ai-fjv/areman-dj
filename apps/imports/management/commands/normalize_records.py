#!/usr/bin/env python3

# apps/imports/management/commands/normalize_records.py
"""
Purpose:
    Normalize all ImportRawRecords for a given supplier where ImportRun.map_set is NULL,
    or reprocess a specific ImportRun when --run-id is provided.

Usage:
    python manage.py normalize_records --supplier 70002
    python manage.py normalize_records --run-id 15

Behavior:
    - If --run-id is given:
        * Clears normalized_data + error_message_product_import for all records of that run.
        * Processes only this ImportRun.
    - Otherwise:
        * Finds newest ImportMapSet for the supplier + source_type of each ImportRun
          where map_set is NULL.
        * Sets ImportRun.map_set if not already set.
        * Normalizes all ImportRawRecords with `normalized_data IS NULL` in batches.
    - Loads defaults first, then applies supplier mapping (overwriting).
    - Logs processed counts (success vs. error).
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
from apps.imports.services.merge_defaults import load_defaults

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Normalize ImportRawRecords for a supplier (or specific ImportRun)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--supplier",
            help="Supplier code (e.g. 70002). Ignored if --run-id is used.",
        )
        parser.add_argument(
            "--run-id",
            type=int,
            help="Optional: reprocess this specific ImportRun id instead of supplier-wide processing.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        run_id = options.get("run_id")
        supplier_code = options.get("supplier")

        if run_id:
            try:
                run = ImportRun.objects.get(id=run_id)
            except ImportRun.DoesNotExist:
                raise CommandError(f"ImportRun {run_id} not found")

            # reset normalized_data + error field
            ImportRawRecord.objects.filter(import_run=run).update(
                normalized_data=None, error_message_product_import=None
            )
            runs = [run]

        else:
            if not supplier_code:
                raise CommandError("You must provide either --supplier or --run-id")

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
                    supplier=run.supplier,
                    source_type=run.source_type,
                )
                .order_by("-valid_from")
                .first()
            )

            if not map_set:
                raise CommandError(
                    f"No ImportMapSet found for supplier={run.supplier.supplier_code}, "
                    f"source_type={run.source_type.code}"
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
                    # load defaults first
                    normalized = load_defaults(map_set.organization)

                    # apply supplier mapping and overwrite defaults
                    mapped = apply_mapping(rec.payload, map_set)
                    normalized.update(mapped)

                    rec.normalized_data = normalized
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

            self.stdout.write(
                self.style.SUCCESS(
                    f"Processed ImportRun {run.id}: {success_count} success, "
                    f"{error_count} errors with map_set {map_set.id}."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {total_runs} runs processed, {total_success} records normalized, {total_errors} errors."
            )
        )
