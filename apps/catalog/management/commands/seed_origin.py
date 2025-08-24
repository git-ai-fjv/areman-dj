#!/usr/bin/env python3
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations

import logging
import traceback
from typing import List, Tuple

from django.core.management.base import BaseCommand, CommandError
from apps.catalog.models.origin import Origin

logger = logging.getLogger(__name__)


def parse_items(raw: str) -> List[Tuple[str, str]]:
    """Parse a string like 'E:EU, N:Non-EU' into a list of (code, description).

    Rules:
      - Code must be exactly one character (after stripping), will be uppercased.
      - Description is optional; empty becomes ''.
      - Items are comma-separated; each item is 'code:description'.
    """
    items: List[Tuple[str, str]] = []
    if not raw:
        return items
    for chunk in raw.split(","):
        part = chunk.strip()
        if not part:
            continue
        if ":" not in part:
            raise ValueError(f"Invalid item '{part}'. Use format code:description")
        code_str, desc = part.split(":", 1)
        code = code_str.strip().upper()
        if len(code) != 1:
            raise ValueError(f"Origin code must be exactly 1 character, got '{code_str}'")
        items.append((code, desc.strip()))
    return items


class Command(BaseCommand):
    """Upsert Origin records by origin_code (CHAR(1))."""

    help = "Upsert origins. Usage: --items 'E:EU,N:Non-EU' [--dry-run]"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--items",
            type=str,
            default="",
            help="Comma-separated pairs 'code:description', e.g. 'E:EU,N:Non-EU'.",
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
                raise CommandError("No items provided. Use --items 'E:EU,N:Non-EU'.")

            created = 0
            updated = 0
            for code, desc in items:
                if dry_run:
                    self.stdout.write(f"[DRY] would upsert code={code!r}, description={desc!r}")
                    continue

                obj, was_created = Origin.objects.update_or_create(
                    origin_code=code,
                    defaults={"origin_description": desc[:100]},
                )
                if was_created:
                    created += 1
                    self.stdout.write(f"Created origin {obj.origin_code}")
                else:
                    updated += 1
                    self.stdout.write(f"Updated origin {obj.origin_code}")

            if dry_run:
                self.stdout.write(self.style.SUCCESS("Dry run complete. No changes applied."))
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}.")
                )

        except Exception as e:
            tb = traceback.format_exc()
            logger.warning(f"Seed origins failed: {e}")
            raise CommandError(f"Error seeding origins: {e}\n{tb}")

