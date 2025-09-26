# apps/core/management/commands/seed_currency.py
"""
Management command to seed or update Currency records in the database.

This command supports both direct item strings (via --items) and external
files (via --file). Each currency is defined in a compact colon-delimited
format:

    code:name[:symbol][:decimal_places][:active]

Arguments:
  --items   Comma-separated entries with the above format.
  --file    Path to a text file containing one entry per line.
  --dry-run Validate and parse input without persisting any changes.

Behavior:
  • Upserts currencies by primary key 'code' (ISO-4217).
  • Default values: symbol="", decimal_places=2, active=True.
  • Input is validated and trimmed to model field length constraints.
  • Provides summary of created/updated records or dry-run output.

Examples:
  python manage.py seed_currency --items "EUR:Euro:€:2,USD:US Dollar:$:2"
  python manage.py seed_currency --file scripts/currencies.txt
"""


# python manage.py seed_currency --items "EUR:Euro:€:2,USD:US Dollar:$:2,GBP:Pound Sterling:£:2"

from __future__ import annotations

import logging
import traceback
from pathlib import Path
from typing import List, Optional, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models.currency import Currency

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

_TRUE = {"1", "true", "t", "yes", "y"}
_FALSE = {"0", "false", "f", "no", "n"}


def _parse_bool(token: str, default: Optional[bool] = None) -> bool:
    t = (token or "").strip().lower()
    if t == "" and default is not None:
        return default
    if t in _TRUE:
        return True
    if t in _FALSE:
        return False
    raise ValueError(f"Invalid boolean value: '{token}'")


def _parse_decimal_places(token: str, default: int = 2) -> int:
    t = (token or "").strip()
    if t == "":
        return default
    try:
        v = int(t)
    except ValueError as e:
        raise ValueError(f"Invalid decimal_places value: '{token}'") from e
    if not (0 <= v <= 6):
        raise ValueError("decimal_places must be between 0 and 6")
    return v


def _read_lines_file(path: Path) -> List[str]:
    lines: List[str] = []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            lines.append(line)
    return lines


def parse_items(raw: str) -> List[Tuple[str, str, str, int, Optional[bool]]]:
    """
    Parse colon-delimited currencies.

    Per item (5 fields max; last 2 optional):
      code:name[:symbol][:decimal_places][:active]

    Defaults:
      symbol          = ""
      decimal_places  = 2
      active          = True

    Returns list of tuples:
      (code, name, symbol, decimal_places, active_or_None)
    """
    items: List[Tuple[str, str, str, int, Optional[bool]]] = []
    if not raw:
        return items

    for chunk in raw.split(","):
        part = chunk.strip()
        if not part:
            continue

        bits = part.split(":", 4)  # up to 5 parts
        if len(bits) < 2:
            raise ValueError("Use 'code:name[:symbol][:decimal_places][:active]'")

        code = (bits[0] or "").strip().upper()
        name = (bits[1] or "").strip()
        symbol = (bits[2].strip() if len(bits) >= 3 else "")
        dp_tok = (bits[3].strip() if len(bits) >= 4 else "")
        active_tok = (bits[4].strip() if len(bits) >= 5 else "")

        if not code or len(code) != 3 or not code.isalpha():
            raise ValueError(f"Currency code must be 3 letters (got '{code}')")
        if not name:
            raise ValueError("Currency name is required")

        decimal_places = _parse_decimal_places(dp_tok, default=2)
        active_val = _parse_bool(active_tok, default=True) if active_tok != "" else None

        # Trim to model limits
        name = name[:100]
        symbol = symbol[:8]

        items.append((code, name, symbol, decimal_places, active_val))
    return items


# ------------------------------------------------------------------------------
# Command
# ------------------------------------------------------------------------------

class Command(BaseCommand):
    """
    Upsert Currency rows by primary key 'code' (ISO-4217).
    """

    help = """Upsert currencies from colon-delimited items or a file.

Format per item:
  code:name[:symbol][:decimal_places][:active]
Defaults: symbol="", decimal_places=2, active=True

Examples:
  --items "EUR:Euro:€:2,USD:US Dollar:$:2,GBP:Pound Sterling:£:2,CHF:Swiss Franc:CHF:2,TRY:Turkish Lira:₺:2"
  --file scripts/currencies.txt
"""

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--items",
            type=str,
            default="",
            help="Comma-separated entries 'code:name[:symbol][:decimal_places][:active]'.",
        )
        parser.add_argument(
            "--file",
            type=str,
            default="",
            help="Path to a newline-delimited file with the same per-line format.",
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
                    "Format: code:name[:symbol][:decimal_places][:active]"
                )

            parsed = parse_items(",".join(raw_lines))

            created = 0
            updated = 0

            for code, name, symbol, decimal_places, active_val in parsed:
                if dry_run:
                    self.stdout.write(
                        f"[DRY] would upsert code={code} name='{name}' symbol='{symbol}' "
                        f"decimal_places={decimal_places} active={active_val if active_val is not None else True}"
                    )
                    continue

                obj, was_created = Currency.objects.update_or_create(
                    code=code,
                    defaults={
                        "name": name,
                        "symbol": symbol or None,
                        "decimal_places": decimal_places,
                        "is_active": active_val if active_val is not None else True,
                    },
                )

                if was_created:
                    created += 1
                    self.stdout.write(f"Created currency {obj.code} ({obj.name})")
                else:
                    updated += 1
                    self.stdout.write(f"Updated currency {obj.code} ({obj.name})")

            if dry_run:
                self.stdout.write(self.style.SUCCESS("Dry run complete. No changes applied."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}."))

        except Exception as e:
            tb = traceback.format_exc()
            logger.warning(f"Seed currencies failed: {e}")
            # Always include traceback per project rules
            raise CommandError(f"Error seeding currencies: {e}\n{tb}")


#
# # scripts/currencies.txt
# # code:name[:symbol][:decimal_places][:active]
# EUR:Euro:€:2
# USD:US Dollar:$:2
# GBP:Pound Sterling:£:2
# CHF:Swiss Franc:CHF:2
# TRY:Turkish Lira:₺:2
#
# python manage.py seed_currency --file scripts/currencies.txt
# # or
# python manage.py seed_currency --items "EUR:Euro:€:2,USD:US Dollar:$:2,GBP:Pound Sterling:£:2"