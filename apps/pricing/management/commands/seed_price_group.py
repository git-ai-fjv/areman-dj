#!/usr/bin/env python3

# apps/pricing/management/commands/seed_price_groups.py
"""
Purpose:
    Management command to upsert PriceGroup records into the database from a
    colon-delimited string. Supports dry-run mode for validation.

Context:
    Part of the `apps.pricing` app. Provides a simple seeding mechanism for
    organizations’ price groups via the Django management interface.

Used by:
    - Initial data setup (seeding default or test price groups)
    - Automated deployment or import pipelines where price groups must exist

Depends on:
    - apps.core.models.Organization
    - apps.pricing.models.PriceGroup
    - Django BaseCommand, transaction handling, CommandError

Example:
    python manage.py seed_price_groups --items "1:PG01:Retail,1::No group"
    python manage.py seed_price_groups --items "1:PG01:Retail" --dry-run
"""


from __future__ import annotations

import logging
import traceback
from typing import List, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models.organization import Organization
from apps.pricing.models.price_group import PriceGroup

logger = logging.getLogger(__name__)


def parse_items(raw: str) -> List[Tuple[int, str, str]]:
    """Parse a string like '1:PG01:Retail,1::No group' into triplets.

    Format per item: 'org_code:price_group_code[:description]'
      - org_code: integer (SMALLINT)
      - price_group_code: may be empty (''), max length 20
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
        # Allow empty code (''); only enforce max length
        if len(code) > 20:
            raise ValueError(
                f"price_group_code too long ({len(code)}). Max is 20: '{code}'"
            )

        org_code = int(org_str)
        items.append((org_code, code, desc[:200]))
    return items


class Command(BaseCommand):
    """Upsert PriceGroup rows by (organization, price_group_code)."""

    help = (
        "Upsert price groups. Usage:\n"
        '  --items "1:PG01:Retail,1::No group" [--dry-run]\n'
        "Each item is 'org_code:price_group_code[:description]'. "
        "price_group_code may be empty ('')."
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
                    'No items provided. Use --items "1:PG01:Retail,1::No group".'
                )

            created = 0
            updated = 0

            for org_code, code, desc in items:
                if dry_run:
                    self.stdout.write(
                        f"[DRY] would upsert org={org_code}, price_group='{code}', "
                        f"description='{desc}'"
                    )
                    continue

                # Ensure the organization exists (FK to core.Organization.org_code)
                try:
                    org = Organization.objects.get(org_code=org_code)
                except Organization.DoesNotExist:
                    raise CommandError(
                        f"Organization with org_code={org_code} does not exist."
                    )

                obj, was_created = PriceGroup.objects.update_or_create(
                    organization=org,
                    price_group_code=code,
                    defaults={"price_group_description": desc},
                )
                if was_created:
                    created += 1
                    self.stdout.write(
                        f"Created price_group {obj.price_group_code} (org={org_code})"
                    )
                else:
                    updated += 1
                    self.stdout.write(
                        f"Updated price_group {obj.price_group_code} (org={org_code})"
                    )

            if dry_run:
                self.stdout.write(self.style.SUCCESS("Dry run complete. No changes applied."))
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}.")
                )

        except Exception as e:
            tb = traceback.format_exc()
            logger.warning(f"Seed price groups failed: {e}")
            # Always include traceback in the error message as per project rules
            raise CommandError(f"Error seeding price groups: {e}\n{tb}")

