# apps/catalog/management/commands/seed_channel_variant.py
# apps/catalog/management/commands/seed_channel_variant.py
"""
Purpose:
    Management command to upsert (create or update) ChannelVariant rows,
    linking product variants to sales channels. Supports colon-delimited input
    from CLI or file, including publish flags, active states, update markers,
    and optional external IDs from shop systems.

Context:
    Part of the catalog app. Extends seeding of channels by assigning which
    product variants are available in which channels (e.g. Webshop, Amazon).
    Used during initial data setup or ongoing synchronization with external
    sales platforms.

Used by:
    - Administrators to seed product-channel relations.
    - Deployment scripts for initializing sales channel variants.
    - Support staff for one-off updates to channel-variant publishing states.

Depends on:
    - apps.core.models.Organization (to resolve org by org_code).
    - apps.catalog.models.Channel (to resolve channels by code or id).
    - apps.catalog.models.ProductVariant (to resolve product variants by SKU or id).
    - apps.catalog.models.ChannelVariant (target table for persistence).

Example:
    # Dry run (validate only)
    python manage.py seed_channel_variant --file scripts/channel_variants.txt --dry-run

    # Apply from file
    python manage.py seed_channel_variant --file scripts/channel_variants.txt

    # One-off inline seeding
    python manage.py seed_channel_variant --items "1:WEB:SKU-1001:1:1:0,1:AMZ:SKU-2002:::1::AMZ-2002"
"""


from __future__ import annotations

import logging
import traceback
from pathlib import Path
from typing import List, Optional, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models.organization import Organization
from apps.catalog.models.channel import Channel
from apps.catalog.models.product_variant import ProductVariant
from apps.catalog.models.channel_variant import ChannelVariant

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


def parse_items(raw: str) -> List[Tuple[int, str, str, bool, bool, bool, Optional[str], Optional[str]]]:
    """
    Parse colon-delimited channel variants.

    Per item (up to 8 fields; last 5 optional):
      org_code:channel_code:sku[:publish][:is_active][:need_shop_update][:shop_item_id][:shop_variant_id]

    Defaults:
      publish         = False
      is_active       = True
      need_shop_update= False
      shop_item_id    = NULL
      shop_variant_id = NULL
    """
    items: List[Tuple[int, str, str, bool, bool, bool, Optional[str], Optional[str]]] = []
    if not raw:
        return items

    for chunk in raw.split(","):
        part = chunk.strip()
        if not part:
            continue

        bits = part.split(":", 7)  # up to 8 parts
        if len(bits) < 3:
            raise ValueError(
                f"Invalid item '{part}'. "
                "Use 'org:channel_code:sku[:publish][:is_active][:need_shop_update][:shop_item_id][:shop_variant_id]'"
            )

        org_str = bits[0].strip()
        ch_code = (bits[1] or "").strip()
        sku_or_id = (bits[2] or "").strip()

        pub_tok = (bits[3].strip() if len(bits) >= 4 else "")
        act_tok = (bits[4].strip() if len(bits) >= 5 else "")
        need_tok = (bits[5].strip() if len(bits) >= 6 else "")
        shop_item_id = (bits[6].strip() if len(bits) >= 7 else "") or None
        shop_variant_id = (bits[7].strip() if len(bits) >= 8 else "") or None

        if not org_str or not ch_code or not sku_or_id:
            raise ValueError(f"Missing org, channel_code or sku in '{part}'")

        org_code = int(org_str)
        publish = _parse_bool(pub_tok, default=False) if pub_tok != "" else False
        is_active = _parse_bool(act_tok, default=True) if act_tok != "" else True
        need_shop_update = _parse_bool(need_tok, default=False) if need_tok != "" else False

        # Trim external ids to model limits (100)
        if shop_item_id:
            shop_item_id = shop_item_id[:100]
        if shop_variant_id:
            shop_variant_id = shop_variant_id[:100]

        items.append((org_code, ch_code[:20], sku_or_id[:120], publish, is_active, need_shop_update, shop_item_id, shop_variant_id))
    return items


# ------------------------------------------------------------------------------
# Command
# ------------------------------------------------------------------------------

class Command(BaseCommand):
    """
    Upsert ChannelVariant rows by unique (organization, channel, variant).

    By default, this command resolves:
      - channel by (organization, channel_code)
      - variant by (organization, sku)

    Tip: If you prefer numeric lookups, you can pass channel_code as a numeric id
         and/or sku as a numeric variant id; the command will try id fallback if
         a code/sku lookup fails.
    """

    help = """Upsert channel variants from colon-delimited items or a file.

Format per item:
  org:channel_code:sku[:publish][:is_active][:need_shop_update][:shop_item_id][:shop_variant_id]

Defaults: publish=False, is_active=True, need_shop_update=False, external ids empty.

Examples:
  --items "1:WEB:SKU-1001:1:1:0,1:AMZ:SKU-2002:::1::AMZ-2002"
  --file scripts/channel_variants.txt
"""

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--items",
            type=str,
            default="",
            help="Comma-separated entries 'org:channel_code:sku[:publish][:is_active][:need_update][:shop_item_id][:shop_variant_id]'.",
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
                    "Format: org:channel_code:sku[:publish][:is_active][:need_update][:shop_item_id][:shop_variant_id]"
                )

            parsed = parse_items(",".join(raw_lines))

            created = 0
            updated = 0

            for org_code, ch_code, sku_or_id, publish, is_active, need_update, shop_item_id, shop_variant_id in parsed:
                # Resolve org
                try:
                    org = Organization.objects.get(org_code=org_code)
                except Organization.DoesNotExist:
                    raise CommandError(f"Organization with org_code={org_code} does not exist.")

                # Resolve channel: try by code, then by numeric id (scoped to org)
                channel = Channel.objects.filter(organization=org, channel_code=ch_code).first()
                if channel is None and ch_code.isdigit():
                    channel = Channel.objects.filter(organization=org, id=int(ch_code)).first()
                if channel is None:
                    raise CommandError(f"Channel '{ch_code}' not found for org={org_code} (by code or id).")

                # Resolve variant: try by sku, then by numeric id (scoped to org)
                variant = ProductVariant.objects.filter(organization=org, sku=sku_or_id).first()
                if variant is None and sku_or_id.isdigit():
                    variant = ProductVariant.objects.filter(organization=org, id=int(sku_or_id)).first()
                if variant is None:
                    raise CommandError(f"Variant '{sku_or_id}' not found for org={org_code} (by SKU or id).")

                if dry_run:
                    self.stdout.write(
                        f"[DRY] would upsert org={org_code} ch={channel.id}/{channel.channel_code} "
                        f"var={variant.id}/{variant.sku} publish={publish} active={is_active} "
                        f"need_update={need_update} shop_item_id={shop_item_id} shop_variant_id={shop_variant_id}"
                    )
                    continue

                obj, was_created = ChannelVariant.objects.update_or_create(
                    organization=org,
                    channel=channel,
                    variant=variant,
                    defaults={
                        "publish": publish,
                        "is_active": is_active,
                        "need_shop_update": need_update,
                        "shop_item_id": shop_item_id,
                        "shop_variant_id": shop_variant_id,
                    },
                )

                if was_created:
                    created += 1
                    self.stdout.write(
                        f"Created channel_variant id={obj.id} org={org_code} "
                        f"ch={channel.channel_code} var={variant.sku} publish={publish}"
                    )
                else:
                    updated += 1
                    self.stdout.write(
                        f"Updated channel_variant id={obj.id} org={org_code} "
                        f"ch={channel.channel_code} var={variant.sku} publish={publish}"
                    )

            if dry_run:
                self.stdout.write(self.style.SUCCESS("Dry run complete. No changes applied."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}."))

        except Exception as e:
            tb = traceback.format_exc()
            logger.warning(f"Seed channel variants failed: {e}")
            # Always include traceback per project rules
            raise CommandError(f"Error seeding channel variants: {e}\n{tb}")

# # scripts/channel_variants.txt
# # org:channel_code:sku[:publish][:is_active][:need_update][:shop_item_id][:shop_variant_id]
# 1:WEB:SKU-1001:1:1:0
# 1:WEB:SKU-2002:::1
# 1:AMZ:SKU-2002:::1::AMZ-2002
#
# # dry run
# python manage.py seed_channel_variant --file scripts/channel_variants.txt --dry-run
#
# # apply
# python manage.py seed_channel_variant --file scripts/channel_variants.txt
#
# # one-off via --items
# python manage.py seed_channel_variant --items "1:WEB:SKU-1001:1:1:0,1:AMZ:SKU-2002:::1::AMZ-2002"
