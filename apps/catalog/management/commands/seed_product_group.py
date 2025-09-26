# apps/catalog/management/commands/seed_product_group.py
#!/usr/bin/env python3
# apps/catalog/management/commands/seed_product_group.py
"""
Purpose:
    Management command to upsert ProductGroup records by (organization, product_group_code).
    Enables seeding and maintaining product groups per organization in a consistent, idempotent way.

Context:
    Part of the catalog seeding workflow. Used during initial setup, imports, or
    synchronization steps to define or adjust logical product groupings (e.g. Hardware,
    Accessories, No group).

Used by:
    - Administrators when bootstrapping catalog structures.
    - ETL/import processes that need to ensure required product groups exist.
    - Developers when preparing test data for local development.

Depends on:
    - apps.core.models.organization.Organization (for org scoping).
    - apps.catalog.models.product_group.ProductGroup (target model).

Key Features:
    - Accepts colon-delimited items: org_code:product_group_code[:description].
    - Supports empty product_group_code to represent “no group”.
    - Validates code length (max 20 chars) and description length (max 200 chars).
    - Idempotent upsert via `update_or_create`.
    - Supports dry-run mode for safe validation.
    - Runs inside an atomic transaction for batch safety.

Examples:
    # Dry run
    python manage.py seed_product_group --items "1:GRP01:Hardware,1::No group" --dry-run

    # Apply changes
    python manage.py seed_product_group --items "1:GRP01:Hardware,1::No group"
"""

from __future__ import annotations

import logging
import traceback
from typing import List, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models.organization import Organization
from apps.catalog.models.product_group import ProductGroup

logger = logging.getLogger(__name__)


def parse_items(raw: str) -> List[Tuple[int, str, str]]:
    """Parse a string like '1:GRP01:Hardware,1::No group' into triplets.

    Format per item: 'org_code:product_group_code[:description]'
      - org_code: integer (SMALLINT)
      - product_group_code: may be empty (''), max length 20
      - description: optional, will be trimmed to 200 chars
    Items are comma-separated.
    """
    items: List[Tuple[int, str, str]] = []
    if not raw:
        return items

    for chunk in raw.split(","):
        part = chunk.strip()
        if not part:
            continue

        bits = part.split(":", 2)  # up to 3 parts
        if len(bits) < 2:
            raise ValueError(f"Invalid item '{part}'. Use 'org:code[:description]'")

        org_str, code = bits[0].strip(), bits[1].strip()
        desc = bits[2].strip() if len(bits) == 3 else ""

        if not org_str:
            raise ValueError(f"Missing org_code in '{part}'")
        if len(code) > 20:
            raise ValueError(
                f"product_group_code too long ({len(code)}). Max is 20: '{code}'"
            )

        org_code = int(org_str)
        items.append((org_code, code, desc[:200]))
    return items


class Command(BaseCommand):
    """Upsert ProductGroup rows by (organization, product_group_code)."""

    help = (
        "Upsert product groups. Usage:\n"
        '  --items "1:GRP01:Hardware,1::No group" [--dry-run]\n'
        "Each item is 'org_code:product_group_code[:description]'. "
        "product_group_code may be empty ('')."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--items",
            type=str,
            default="",
            help="Comma-separated entries 'org:code[:description]'. code may be empty ('').",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and validate, but do not write to the database.",
        )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        raw_items: str = options["items"]
        dry_run: bool = options["dry_run"]

        try:
            items = parse_items(raw_items)
            if not items:
                raise CommandError(
                    'No items provided. Use --items "1:GRP01:Hardware,1::No group".'
                )

            created = 0
            updated = 0

            for org_code, code, desc in items:
                if dry_run:
                    self.stdout.write(
                        f"[DRY] would upsert org={org_code}, product_group='{code}', "
                        f"description='{desc}'"
                    )
                    continue

                try:
                    org = Organization.objects.get(org_code=org_code)
                except Organization.DoesNotExist:
                    raise CommandError(
                        f"Organization with org_code={org_code} does not exist."
                    )

                obj, was_created = ProductGroup.objects.update_or_create(
                    organization=org,
                    product_group_code=code,
                    defaults={"product_group_description": desc},
                )
                if was_created:
                    created += 1
                    self.stdout.write(
                        f"Created product_group {obj.product_group_code} (org={org_code})"
                    )
                else:
                    updated += 1
                    self.stdout.write(
                        f"Updated product_group {obj.product_group_code} (org={org_code})"
                    )

            if dry_run:
                self.stdout.write(self.style.SUCCESS("Dry run complete. No changes applied."))
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}.")
                )

        except Exception as e:
            tb = traceback.format_exc()
            logger.warning(f"Seed product groups failed: {e}")
            raise CommandError(f"Error seeding product groups: {e}\n{tb}")


