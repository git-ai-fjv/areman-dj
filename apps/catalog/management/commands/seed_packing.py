#!/usr/bin/env python3

# apps/catalog/management/commands/seed_packing.py
"""
Purpose:
    Management command to upsert (create or update) Packing records
    for packaging units such as boxes, pallets, or pieces.
    Input is colon-delimited and strictly follows the original SQL
    column order: org_code : packing_code : amount : short_desc [: long_desc].

Context:
    Part of the catalog app. Provides standardized seeding of packing units
    across organizations, ensuring that ERP and webshop share the same
    base packing definitions. Critical for quantity handling and
    procurement consistency.

Used by:
    - Administrators to seed initial packing units.
    - Deployment/support scripts to maintain consistent packing codes.
    - Developers during testing or setup when new packings are required.

Depends on:
    - apps.core.models.organization.Organization (FK resolution).
    - apps.catalog.models.packing.Packing (target table).
    - Python Decimal for fractional amounts (quantized to 3 decimals).
    - Django ORM update_or_create for idempotent upserts.

Example:
    # Dry run (no DB changes)
    python manage.py seed_packing --items "1:1:1:BX" --dry-run

    # Apply simple packings
    python manage.py seed_packing --items "1:1:1:BX,1:2:1:piece"

    # Apply with long description
    python manage.py seed_packing --items "2:30:0.125:PAL:Standard pallet"
"""


from __future__ import annotations

import logging
import traceback
from decimal import Decimal, InvalidOperation
from typing import List, Tuple

from django.core.management.base import BaseCommand, CommandError

from apps.core.models.organization import Organization
from apps.catalog.models.packing import Packing

logger = logging.getLogger(__name__)


def _parse_smallint(value: str) -> int:
    """Parse a string into a PostgreSQL SMALLINT-compatible int (0..32767)."""
    value = value.strip()
    if value == "":
        raise ValueError("Empty integer value")
    try:
        iv = int(value, 10)
    except ValueError as exc:
        raise ValueError(f"Invalid integer: {value!r}") from exc
    if iv < 0 or iv > 32767:
        raise ValueError(f"Value out of SMALLINT range (0..32767): {iv}")
    return iv


def _parse_amount(value: str) -> Decimal:
    """Parse a decimal with 3 fraction digits. Accepts ',' or '.' as decimal separator."""
    txt = value.strip().replace(",", ".")
    if txt == "":
        raise ValueError("Amount must not be empty")
    try:
        d = Decimal(txt)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal amount: {value!r}") from exc
    # Normalize/limit to 3 decimal places
    return d.quantize(Decimal("0.001"))


def parse_items(raw: str) -> List[Tuple[int, int, Decimal, str, str]]:
    """Parse '--items' into (org_code, packing_code, amount, short_desc, long_desc).

    STRICT ORDER — matches original SQL column order:
        org_code : packing_code : amount : short_desc [: long_desc]

    Rules:
      - org_code, packing_code: SMALLINT (0..32767), required.
      - amount: required decimal (3 fraction digits); '.' or ',' accepted.
      - short_desc: required, max 20 chars.
      - long_desc: optional, max 200 chars.
      - Whitespace around fields is trimmed.
      - Comma separates items; commas are not allowed inside fields.
    """
    items: List[Tuple[int, int, Decimal, str, str]] = []
    if not raw:
        return items

    for chunk in raw.split(","):
        part = chunk.strip()
        if not part:
            continue

        pieces = [p.strip() for p in part.split(":")]
        if len(pieces) not in (4, 5):
            raise ValueError(
                f"Invalid item '{part}'. Use 'org:code:amount:short[:long]'."
            )

        org_code = _parse_smallint(pieces[0])
        packing_code = _parse_smallint(pieces[1])

        amount = _parse_amount(pieces[2])

        short = pieces[3].strip()
        if not short:
            raise ValueError(f"Short description must not be empty in '{part}'.")
        if len(short) > 20:
            raise ValueError(f"Short description too long (max 20): {short!r}")

        long = pieces[4].strip() if len(pieces) == 5 else ""
        if len(long) > 200:
            raise ValueError(f"Long description too long (max 200): {long!r}")

        items.append((org_code, packing_code, amount, short, long))

    return items


class Command(BaseCommand):
    """Upsert Packing records by (organization, packing_code)."""

    help = (
        "Upsert packing units (STRICT order matching original SQL):\n"
        "  --items 'org:code:amount:short[:long]'\n"
        "Examples:\n"
        "  --items '1:1:1:BX'\n"
        "  --items '1:2:1:piece'\n"
        "  --items '2:30:0.125:PAL:Standard pallet'\n"
        "Notes:\n"
        "  - Amount is required; accepts '.' or ','.\n"
        "  - Comma separates items; do not use commas inside fields."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--items",
            type=str,
            default="",
            help="Comma-separated items in the form 'org:code:amount:short[:long]'.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and validate, but do not write to the database.",
        )

    def handle(self, *args, **options) -> None:
        raw_items: str = options["items"]
        dry_run: bool = options["dry_run"]

        try:
            items = parse_items(raw_items)
            if not items:
                raise CommandError(
                    "No items provided. Use --items 'org:code:amount:short[:long]'."
                )

            created = 0
            updated = 0

            for org_code, packing_code, amount, short, long in items:
                if dry_run:
                    self.stdout.write(
                        f"[DRY] would upsert org={org_code}, code={packing_code}, "
                        f"amount={amount}, short={short!r}, long={long!r}"
                    )
                    continue

                # Ensure organization exists (clear error if not)
                if not Organization.objects.filter(org_code=org_code).exists():
                    raise CommandError(
                        f"Organization {org_code} does not exist. Seed 'org' first."
                    )

                # Use organization_id to match FK by Organization PK (org_code)
                obj, was_created = Packing.objects.update_or_create(
                    organization_id=org_code,
                    packing_code=packing_code,
                    defaults={
                        "amount": amount,
                        "packing_short_description": short,
                        "packing_description": long or "",
                    },
                )

                if was_created:
                    created += 1
                    self.stdout.write(
                        f"Created packing org={org_code}, code={obj.packing_code}"
                    )
                else:
                    updated += 1
                    self.stdout.write(
                        f"Updated packing org={org_code}, code={obj.packing_code}"
                    )

            if dry_run:
                self.stdout.write(self.style.SUCCESS("Dry run complete. No changes applied."))
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}.")
                )

        except Exception as e:
            tb = traceback.format_exc()
            logger.warning(f"Seed packing failed: {e}")
            raise CommandError(f"Error seeding packing: {e}\n{tb}")
