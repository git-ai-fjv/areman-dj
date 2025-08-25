#!/usr/bin/env python3
# apps/core/management/commands/seed_organization.py
# Created according to the user's permanent Copilot Base Instructions.

from __future__ import annotations

import logging
import traceback
from pathlib import Path
from typing import List, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models.organization import Organization

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def _read_lines_file(path: Path) -> List[str]:
    lines: List[str] = []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            lines.append(line)
    return lines


def parse_items(raw: str) -> List[Tuple[int, str]]:
    """
    Parse colon-delimited organizations.

    Format: org_code:description
    Example: "1:Main Org,2:Test Mandant"
    """
    items: List[Tuple[int, str]] = []
    if not raw:
        return items

    for chunk in raw.split(","):
        part = chunk.strip()
        if not part:
            continue

        bits = part.split(":", 1)
        if len(bits) != 2:
            raise ValueError("Use format 'org_code:description'")

        try:
            org_code = int(bits[0])
        except ValueError as e:
            raise ValueError(f"Invalid org_code '{bits[0]}', must be int") from e

        description = bits[1].strip()
        if not description:
            raise ValueError("Organization description is required")

        description = description[:200]  # trim to model limit
        items.append((org_code, description))
    return items


# -------------------------------------------------------------------
# Command
# -------------------------------------------------------------------
class Command(BaseCommand):
    """
    Upsert Organization rows by primary key 'org_code'.
    """

    help = """Upsert organizations from colon-delimited items or a file.

Format: org_code:description

Examples:
  --items "1:Main Org,2:Test Mandant"
  --file scripts/organizations.txt
"""

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--items",
            type=str,
            default="",
            help="Comma-separated entries 'org_code:description'.",
        )
        parser.add_argument(
            "--file",
            type=str,
            default="",
            help="Path to a newline-delimited file with the same format.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and validate, but do not write to the database.",
        )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        items_arg: str = options["items"]
        file_arg: str = options["file"]
        dry_run: bool = options["dry_run"]

        try:
            raw_lines: List[str] = []
            if items_arg:
                raw_lines.extend([p.strip() for p in items_arg.split(",") if p.strip()])
            if file_arg:
                raw_lines.extend(_read_lines_file(Path(file_arg)))

            if not raw_lines:
                raise CommandError(
                    "No items provided. Use --items or --file. "
                    "Format: org_code:description"
                )

            parsed = parse_items(",".join(raw_lines))

            created = 0
            updated = 0

            for org_code, desc in parsed:
                if dry_run:
                    self.stdout.write(f"[DRY] would upsert code={org_code} desc='{desc}'")
                    continue

                obj, was_created = Organization.objects.update_or_create(
                    org_code=org_code,
                    defaults={"org_description": desc},
                )

                if was_created:
                    created += 1
                    self.stdout.write(f"Created organization {obj.org_code} ({obj.org_description})")
                else:
                    updated += 1
                    self.stdout.write(f"Updated organization {obj.org_code} ({obj.org_description})")

            if dry_run:
                self.stdout.write(self.style.SUCCESS("Dry run complete. No changes applied."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}."))

        except Exception as e:
            tb = traceback.format_exc()
            logger.warning(f"Seed organizations failed: {e}")
            raise CommandError(f"Error seeding organizations: {e}\n{tb}")
#
# # direkt mit Items
# python manage.py seed_organization --items "1:Main Org,2:Test Mandant"
#
# # aus Datei
# cat > scripts/organizations.txt <<EOF
# 1:Main Org
# 2:Test Mandant
# EOF
# python manage.py seed_organization --file scripts/organizations.txt
#
# # nur Validierung
# python manage.py seed_organization --items "1:Main Org" --dry-run
