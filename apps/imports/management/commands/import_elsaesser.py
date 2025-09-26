#!/usr/bin/env python3
# apps/imports/management/commands/import_elsaesser.py
"""
Purpose:
    Management command to import products from the Elsässer Filter-Technik Store API
    into the database. Products are first logged in `ImportRun` and stored as raw JSON
    payloads in `ImportRawRecord` for further processing.

Context:
    Part of the `apps.imports` app. Runs as a Django management command.
    Used to synchronize supplier catalogs into the import pipeline.
    Supports dry-run mode for previewing data without database writes.

Used by:
    - Developers (manual execution via `python manage.py import_elsaesser`)
    - Automated import jobs (cron / scheduled tasks)
    - Downstream services that consume `ImportRun` and `ImportRawRecord`

Depends on:
    - apps.imports.api.elsaesser_filter_client.FilterTechnikApiClient (API access)
    - apps.imports.models.ImportRun (import session tracking)
    - apps.imports.models.ImportRawRecord (raw product payloads)
    - apps.imports.models.ImportSourceType (to classify source type)
    - apps.partners.models.Supplier (supplier reference)
    - Django transaction management and logging

Example:
    # Dry run: fetch and preview 50 products without DB writes
    python manage.py import_elsaesser --supplier ELS01 --dry-run --limit 50

    # Real import: insert all products for supplier 'ELS01'
    python manage.py import_elsaesser --supplier ELS01
"""


from __future__ import annotations

import logging
import traceback
import time
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.imports.models.import_run import ImportRun
from apps.imports.models.import_raw_record import ImportRawRecord
from apps.imports.models.import_source_type import ImportSourceType
from apps.partners.models.supplier import Supplier
from apps.imports.api.elsaesser_filter_client import FilterTechnikApiClient, ApiError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Import products from Elsässer Filter-Technik Store API into ImportRun + ImportRawRecord.
    """

    help = """Import products from Elsässer API into ImportRawRecord.

Usage:
  python manage.py import_elsaesser --supplier ELS01 [--dry-run] [--limit 500]

Notes:
  - API limits apply:
      * Daytime (08:00–20:00): ~2000 requests/day
      * Nighttime (20:00–08:00): ~200–300 requests/minute
  - The importer auto-throttles with a short sleep to stay within limits.
"""

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--supplier", required=True, help="Supplier code (e.g., ELS01)"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Fetch and preview products, but do not write to the database.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Optional max number of products to fetch (0 = no limit).",
        )

    def handle(self, *args, **options) -> None:
        supplier_code: str = options["supplier"]
        dry_run: bool = options["dry_run"]
        limit: int = options["limit"]

        try:
            # Supplier prüfen
            try:
                supplier = Supplier.objects.get(supplier_code=supplier_code)
            except Supplier.DoesNotExist:
                raise CommandError(f"Supplier '{supplier_code}' not found")

            # SourceType prüfen
            try:
                source_type = ImportSourceType.objects.get(code="api")
            except ImportSourceType.DoesNotExist:
                raise CommandError("ImportSourceType 'api' not found")

            # Elsässer API client
            BASE_URL = "https://www.filter-technik.de/store-api"
            API_KEY = "SWSCQU9ZETYXSGPTB2DSAFM2WQ"
            USERNAME = "bestellung@areman.de"
            PASSWORD = "1c6a4c1b"

            client = FilterTechnikApiClient(BASE_URL, API_KEY, USERNAME, PASSWORD)
            client.login()

            # ---------------- DRY-RUN ----------------
            if dry_run:
                self.stdout.write(self.style.WARNING("[DRY-RUN] No DB changes."))

                products = []
                page = 1
                per_page = 100
                while True:
                    payload = {"page": page, "limit": per_page}
                    resp = client._post("product", payload, context_token=client.context_token)
                    data = resp.json()
                    elements = data.get("elements", [])

                    if not elements:
                        break

                    products.extend(elements)
                    if limit and len(products) >= limit:
                        break

                    page += 1
                    time.sleep(0.25)

                preview = products[:20]
                for i, p in enumerate(preview, start=1):
                    number = p.get("productNumber")
                    name = (p.get("translated") or {}).get("name")
                    self.stdout.write(f"{i}. {number} — {name}")

                self.stdout.write(
                    f"Total fetched: {len(products)} (showing {len(preview)} preview items)"
                )
                return

            # ---------------- REAL IMPORT ----------------
            run = ImportRun.objects.create(
                supplier=supplier,
                source_type=source_type,
                source_file=None,
                started_at=timezone.now(),
                status="running",
            )

            inserted = 0
            page = 1
            per_page = 100
            line_number = 0

            while True:
                payload = {"page": page, "limit": per_page}
                resp = client._post("product", payload, context_token=client.context_token)
                data = resp.json()
                elements = data.get("elements", [])

                if not elements:
                    break

                # Commit pro Page
                with transaction.atomic():
                    for product in elements:
                        line_number += 1
                        ImportRawRecord.objects.create(
                            import_run=run,
                            line_number=line_number,
                            payload=product,
                            supplier_product_reference=product.get("productNumber"),
                        )
                        inserted += 1

                        if limit and inserted >= limit:
                            break

                # Wichtige Ausgabe: aktuelle Page und Gesamtanzahl
                self.stdout.write(
                    self.style.NOTICE(
                        f"✅ Page {page} complete — total {inserted} products inserted so far."
                    )
                )

                if limit and inserted >= limit:
                    break

                page += 1
                time.sleep(0.25)  # Throttle

            run.finished_at = timezone.now()
            run.total_records = inserted
            run.status = "success"
            run.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f"🎉 ImportRun {run.id} complete — {inserted} products imported."
                )
            )

        except (ApiError, Exception) as e:
            tb = traceback.format_exc()
            logger.error("Elsässer import failed: %s\n%s", e, tb)
            raise CommandError(f"Error during import: {e}\n{tb}")
