#!/usr/bin/env python3

# apps/partners/management/commands/seed_suppliers.py
"""
Purpose:
    Management command to upsert Supplier records into the database based on
    colon-delimited input. Supports parsing and validation of supplier data
    and ensures idempotent updates.

Context:
    Part of the `apps.partners.management.commands` package.
    Used to populate or refresh suppliers for a given organization during
    bootstrapping, testing, or data migrations.

Used by:
    - Manual execution via `python manage.py seed_suppliers`
    - Setup scripts for initializing suppliers in development/test environments

Depends on:
    - apps.core.models.organization.Organization
    - apps.partners.models.supplier.Supplier
    - Django ORM (update_or_create, transaction.atomic)

Example:
    # Create a default test supplier (inactive)
    python manage.py seed_suppliers --items "1:SUPP01:Default dummy Supplier:0"

    # Create multiple suppliers (active + inactive)
    python manage.py seed_suppliers --items "1:SUPP01:Main Supplier:1,1:SUPP02:Backup Supplier:0"
"""


from __future__ import annotations

import logging
import traceback
from typing import List, Tuple, Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models.organization import Organization
from apps.partners.models.supplier import Supplier

logger = logging.getLogger(__name__)

_TRUE = {"1", "true", "t", "yes", "y"}
_FALSE = {"0", "false", "f", "no", "n"}


def _parse_bool(token: str, default: Optional[bool] = None) -> bool:
    """Parse a token into a boolean value."""
    t = (token or "").strip().lower()
    if t == "" and default is not None:
        return default
    if t in _TRUE:
        return True
    if t in _FALSE:
        return False
    raise ValueError(f"Invalid boolean value: '{token}'")


def parse_items(raw: str) -> List[Tuple[int, str, str, Optional[bool]]]:
    """
    Parse string like '1:SUPP01:Default Supplier:0' into (org_code, code, description, active).

    Format per item:
      org_code:supplier_code[:description][:active]

    - org_code: integer (SMALLINT)
    - supplier_code: string (required, max length 20)
    - description: optional string, max 200 chars
    - active: optional bool (1/0, true/false, yes/no)
    """
    items: List[Tuple[int, str, str, Optional[bool]]] = []
    if not raw:
        return items

    for chunk in raw.split(","):
        part = chunk.strip()
        if not part:
            continue

        bits = part.split(":", 3)  # up to 4 parts
        if len(bits) < 2:
            raise ValueError(f"Invalid supplier item '{part}'. Use 'org:code[:desc][:active]'")

        org_str, code = bits[0].strip(), bits[1].strip()
        desc = bits[2].strip() if len(bits) >= 3 else ""
        active_tok = bits[3].strip() if len(bits) == 4 else ""

        if not org_str:
            raise ValueError(f"Missing org_code in '{part}'")
        if not code:
            raise ValueError(f"Missing supplier_code in '{part}'")

        org_code = int(org_str)
        active_val = _parse_bool(active_tok, default=None) if active_tok != "" else None
        items.append((org_code, code, desc[:200], active_val))
    return items


class Command(BaseCommand):
    """Upsert Supplier rows by (organization, supplier_code)."""

    help = (
        "Upsert suppliers. Usage:\n"
        '  --items "1:SUPP01:Default Supplier:0,1:SUPP02:Live Supplier:1"\n'
        "Format per item: org:code[:description][:active]"
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--items",
            type=str,
            default="",
            help="Comma-separated entries 'org:code[:description][:active]'.",
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
                    'No items provided. Example: --items "1:SUPP01:Default Supplier:0"'
                )

            created, updated = 0, 0

            for org_code, code, desc, active_val in items:
                org = Organization.objects.get(org_code=org_code)

                if dry_run:
                    self.stdout.write(
                        f"[DRY] would upsert supplier org={org_code}, code='{code}', "
                        f"desc='{desc}', active={active_val if active_val is not None else True}"
                    )
                    continue

                obj, was_created = Supplier.objects.update_or_create(
                    organization=org,
                    supplier_code=code,
                    defaults={
                        "supplier_description": desc or "Supplier",
                        "is_active": active_val if active_val is not None else True,
                    },
                )
                if was_created:
                    created += 1
                    self.stdout.write(f"Created supplier {obj.supplier_code} (org={org_code})")
                else:
                    updated += 1
                    self.stdout.write(f"Updated supplier {obj.supplier_code} (org={org_code})")

            self.stdout.write(self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}."))

        except Exception as e:
            tb = traceback.format_exc()
            logger.warning(f"Seed suppliers failed: {e}")
            raise CommandError(f"Error seeding suppliers: {e}\n{tb}")

#
# echo "****************** default dummy ********************************"
# python manage.py seed_suppliers --items "1:SUPP01:Default dummy Supplier for tests:0"
