#!/usr/bin/env python3
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations

import logging
import traceback
from typing import List, Tuple

from django.core.management.base import BaseCommand, CommandError
from apps.catalog.models.manufacturer import Manufacturer

logger = logging.getLogger(__name__)


def parse_items(raw: str) -> List[Tuple[int, str]]:
    """Parse a string like '1:ACME,2:Contoso' into a list of (code, description)."""
    items: List[Tuple[int, str]] = []
    if not raw:
        return items
    for chunk in raw.split(","):
        part = chunk.strip()
        if not part:
            continue
        if ":" not in part:
            raise ValueError(f"Invalid item '{part}'. Use format code:description")
        code_str, desc = part.split(":", 1)
        code = int(code_str)
        items.append((code, desc.strip()))
    return items


class Command(BaseCommand):
    """Upsert Manufacturer records by manufacturer_code."""

    help = "Upsert manufacturers. Usage: --items '1:ACME,2:Contoso' [--dry-run]"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--items",
            type=str,
            default="",
            help="Comma-separated pairs 'code:description', e.g. '1:ACME,2:Contoso'.",
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
                    "No items provided. Use --items '1:ACME,2:Contoso'."
                )

            created = 0
            updated = 0
            for code, desc in items:
                if dry_run:
                    self.stdout.write(f"[DRY] would upsert code={code}, description='{desc}'")
                    continue

                obj, was_created = Manufacturer.objects.update_or_create(
                    manufacturer_code=code,
                    defaults={"manufacturer_description": desc},
                )
                if was_created:
                    created += 1
                    self.stdout.write(f"Created manufacturer {obj.manufacturer_code}")
                else:
                    updated += 1
                    self.stdout.write(f"Updated manufacturer {obj.manufacturer_code}")

            if dry_run:
                self.stdout.write(self.style.SUCCESS("Dry run complete. No changes applied."))
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}.")
                )

        except Exception as e:
            tb = traceback.format_exc()
            logger.warning(f"Seed manufacturers failed: {e}")
            raise CommandError(f"Error seeding manufacturers: {e}\n{tb}")

