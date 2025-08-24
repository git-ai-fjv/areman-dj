# apps/catalog/management/commands/seed_channel.py
# Created according to the user's Copilot Base Instructions.
from __future__ import annotations

import logging
import traceback
from pathlib import Path
from typing import List, Optional, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models.organization import Organization
from apps.core.models.currency import Currency
from apps.catalog.models.channel import Channel

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


def _read_lines_file(path: Path) -> List[str]:
    lines: List[str] = []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            lines.append(line)
    return lines


def parse_items(raw: str) -> List[Tuple[int, str, str, str, str, Optional[bool]]]:
    """
    Parse colon-delimited channels.

    Per item (up to 6 fields; last 3 optional):
      org_code:channel_code:channel_name[:kind][:base_currency_code][:active]

    Defaults:
      kind               = "shop"
      base_currency_code = "EUR"   (must exist if used)
      active             = True
    """
    items: List[Tuple[int, str, str, str, str, Optional[bool]]] = []
    if not raw:
        return items

    for chunk in raw.split(","):
        part = chunk.strip()
        if not part:
            continue

        bits = part.split(":", 5)  # up to 6 parts
        if len(bits) < 3:
            raise ValueError(
                f"Invalid item '{part}'. "
                "Use 'org:channel_code:channel_name[:kind][:currency][:active]'"
            )

        org_str = bits[0].strip()
        code = (bits[1] or "").strip()
        name = (bits[2] or "").strip()
        kind = (bits[3].strip() if len(bits) >= 4 and bits[3].strip() else "shop")
        currency_code = (bits[4].strip().upper() if len(bits) >= 5 and bits[4].strip() else "EUR")
        active_tok = (bits[5].strip() if len(bits) >= 6 else "")

        if not org_str or not code or not name:
            raise ValueError(f"Missing org, code, or name in '{part}'")

        org_code = int(org_str)

        # Trim to model limits
        code = code[:20]
        name = name[:200]
        kind = kind[:20]
        if currency_code and len(currency_code) != 3:
            raise ValueError(f"Currency code must be 3 letters (got '{currency_code}')")

        active_val = _parse_bool(active_tok, default=True) if active_tok != "" else None

        items.append((org_code, code, name, kind, currency_code, active_val))
    return items


# ------------------------------------------------------------------------------
# Command
# ------------------------------------------------------------------------------

class Command(BaseCommand):
    """
    Upsert Channel rows by unique (organization, channel_code).
    """

    help = """Upsert channels from colon-delimited items or a file.

Format per item:
  org:channel_code:channel_name[:kind][:base_currency_code][:active]

Defaults: kind="shop", base_currency_code="EUR", active=True.

Examples:
  --items "1:WEB:Webshop:shop:EUR:1,1:AMZ:Amazon:marketplace:EUR:1"
  --file scripts/channels.txt
"""

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--items",
            type=str,
            default="",
            help="Comma-separated entries 'org:code:name[:kind][:currency][:active]'.",
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
                    "Format: org:channel_code:channel_name[:kind][:currency][:active]"
                )

            parsed = parse_items(",".join(raw_lines))

            created = 0
            updated = 0

            for org_code, code, name, kind, currency_code, active_val in parsed:
                # Resolve Organization
                try:
                    org = Organization.objects.get(org_code=org_code)
                except Organization.DoesNotExist:
                    raise CommandError(f"Organization with org_code={org_code} does not exist.")

                # Resolve Currency
                try:
                    currency = Currency.objects.get(code=currency_code)
                except Currency.DoesNotExist:
                    raise CommandError(f"Currency '{currency_code}' does not exist.")

                if dry_run:
                    self.stdout.write(
                        f"[DRY] would upsert org={org_code} code='{code}' name='{name}' "
                        f"kind='{kind}' currency='{currency_code}' "
                        f"active={active_val if active_val is not None else True}"
                    )
                    continue

                obj, was_created = Channel.objects.update_or_create(
                    organization=org,
                    channel_code=code,
                    defaults={
                        "channel_name": name,
                        "kind": kind,
                        "base_currency": currency,
                        "is_active": active_val if active_val is not None else True,
                    },
                )

                if was_created:
                    created += 1
                    self.stdout.write(
                        f"Created channel id={obj.id} org={org_code} code='{code}' ({kind}/{currency_code})"
                    )
                else:
                    updated += 1
                    self.stdout.write(
                        f"Updated channel id={obj.id} org={org_code} code='{code}' ({kind}/{currency_code})"
                    )

            if dry_run:
                self.stdout.write(self.style.SUCCESS("Dry run complete. No changes applied."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}."))

        except Exception as e:
            tb = traceback.format_exc()
            logger.warning(f"Seed channels failed: {e}")
            # Always include traceback per project rules
            raise CommandError(f"Error seeding channels: {e}\n{tb}")
#
# # scripts/channels.txt
# # org:code:name[:kind][:currency][:active]
# 1:WEB:Webshop:shop:EUR:1
# 1:AMZ:Amazon:marketplace:EUR:1
#
# python manage.py seed_channel --file scripts/channels.txt
# # or
# python manage.py seed_channel --items "1:WEB:Webshop:shop:EUR:1,1:POS:Point of Sale::EUR:"
# # (missing kind -> 'shop', missing active -> True)