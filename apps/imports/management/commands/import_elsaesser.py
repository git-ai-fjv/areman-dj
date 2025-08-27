#!/usr/bin/env python3
# apps/imports/management/commands/import_elsaesser.py
# Created according to the user's permanent Copilot Base Instructions.

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

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        supplier_code: str = options["supplier"]
        dry_run: bool = options["dry_run"]
        limit: int = options["limit"]

        try:
            try:
                supplier = Supplier.objects.get(supplier_code=supplier_code)
            except Supplier.DoesNotExist:
                raise CommandError(f"Supplier '{supplier_code}' not found")

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

                products = client.fetch_all_products(limit=50)  # kleine Testmenge
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
                total = data.get("total", 0)

                if not elements:
                    break

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

                self.stdout.write(f"Inserted {inserted} products (page {page}).")

                if limit and inserted >= limit:
                    break

                if page * per_page >= total:
                    break

                page += 1
                time.sleep(0.25)  # Throttle to ~240 requests/min

            run.finished_at = timezone.now()
            run.total_records = inserted
            run.status = "success"
            run.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f"ImportRun {run.id} complete — {inserted} products imported."
                )
            )

        except (ApiError, Exception) as e:
            tb = traceback.format_exc()
            logger.error("Elsässer import failed: %s\n%s", e, tb)
            raise CommandError(f"Error during import: {e}\n{tb}")


#
# API Import Elsässer:
#   python manage.py import_elsaesser --supplier ELS01
#
# Trockenlauf (nur anzeigen, max 20 Produkte):
#   python manage.py import_elsaesser --supplier ELS01 --dry-run
#
# Begrenzen auf 500 Produkte:
#   python manage.py import_elsaesser --supplier ELS01 --limit 500
#


