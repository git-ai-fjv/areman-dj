#!/usr/bin/env python3
# apps/catalog/management/commands/seed_state.py
"""
Purpose:
    Management command to upsert State records. Each State represents a global
    lifecycle or availability flag (e.g. Active, Inactive) and is identified by
    a one-character code.

Context:
    States are referenced by ProductVariant and potentially other catalog
    entities to standardize workflow and status handling. This command seeds or
    updates these global states in an idempotent way.

Used by:
    - Initial system setup to seed required states (e.g., 'A:Active,I:Inactive').
    - Developers/testers preparing demo or test data.
    - Admins or ETL jobs aligning states with external ERP/PIM systems.

Depends on:
    - apps.catalog.models.state.State

Key Features:
    - Colon-delimited input: "code:description".
    - Code must be exactly one uppercase character (CHAR(1)).
    - Description is optional; trimmed to 100 characters.
    - Comma-separated list of multiple states supported.
    - Idempotent upsert by `state_code`.
    - Dry-run mode available for validation only.

Examples:
    # Seed two states (Active, Inactive)
    python manage.py seed_state --items "A:Active,I:Inactive"

    # Dry run to validate input without applying changes
    python manage.py seed_state --items "D:Deleted" --dry-run
"""

from __future__ import annotations

import logging
import traceback
from typing import List, Tuple

from django.core.management.base import BaseCommand, CommandError
from apps.catalog.models.state import State

logger = logging.getLogger(__name__)


def parse_items(raw: str) -> List[Tuple[str, str]]:
    """Parse a string like 'A:Active,I:Inactive' into a list of (code, description).

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
            raise ValueError(f"State code must be exactly 1 character, got '{code_str}'")
        items.append((code, desc.strip()))
    return items


class Command(BaseCommand):
    """Upsert State records by state_code (CHAR(1))."""

    help = "Upsert states. Usage: --items 'A:Active,I:Inactive' [--dry-run]"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--items",
            type=str,
            default="",
            help="Comma-separated pairs 'code:description', e.g. 'A:Active,I:Inactive'.",
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
                raise CommandError("No items provided. Use --items 'A:Active,I:Inactive'.")

            created = 0
            updated = 0
            for code, desc in items:
                if dry_run:
                    self.stdout.write(f"[DRY] would upsert code={code!r}, description={desc!r}")
                    continue

                obj, was_created = State.objects.update_or_create(
                    state_code=code,
                    defaults={"state_description": desc[:100]},
                )
                if was_created:
                    created += 1
                    self.stdout.write(f"Created state {obj.state_code}")
                else:
                    updated += 1
                    self.stdout.write(f"Updated state {obj.state_code}")

            if dry_run:
                self.stdout.write(self.style.SUCCESS("Dry run complete. No changes applied."))
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}.")
                )

        except Exception as e:
            tb = traceback.format_exc()
            logger.warning(f"Seed states failed: {e}")
            raise CommandError(f"Error seeding states: {e}\n{tb}")
