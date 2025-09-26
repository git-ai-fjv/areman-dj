# apps/catalog/management/commands/seed_product_variant.py

# apps/catalog/management/commands/seed_product_variant.py
"""
Purpose:
    Management command to upsert ProductVariant records (SKUs) in the catalog.
    Ensures consistent variant data including SKU, barcode, packing, origin,
    state, customs code, weight, and active status.

Context:
    Part of the catalog seeding/import pipeline. Variants are the sellable units
    tied to a Product and enriched with physical/logistic attributes. This command
    allows bulk initialization and safe re-runs (idempotent upserts).

Used by:
    - Admins or ETL scripts during catalog import.
    - Developers/testers preparing demo product data.
    - Integration jobs syncing SKUs from external ERP/PIM systems.

Depends on:
    - apps.core.models.organization.Organization
    - apps.catalog.models.product.Product
    - apps.catalog.models.product_variant.ProductVariant
    - apps.catalog.models.packing.Packing
    - apps.catalog.models.origin.Origin
    - apps.catalog.models.state.State

Key Features:
    - Colon-delimited input with up to 10 fields:
      org:product_id:sku[:barcode][:packing][:origin][:state][:customs][:weight][:active]
    - Default values if omitted:
        packing=2, origin='E', state='A', customs=0, weight=0, active=True.
    - Validation for lengths (SKU ≤120, barcode ≤64, codes length=1).
    - Reference checks: org, product, packing, origin, and state must exist.
    - Upsert strategy:
        1) Match by (organization, sku).
        2) Fallback: (organization, product, packing, origin, state).
    - Dry-run mode to validate input without applying changes.
    - Transactional safety.

Examples:
    # Minimal SKU with defaults
    python manage.py seed_product_variant --items "1:1001:SKU-123"

    # Full variant with explicit attributes
    python manage.py seed_product_variant --items "1:1001:SKU-124:4006381333931:2:E:A:0:0.250:1"

    # From file
    python manage.py seed_product_variant --file scripts/variants.txt
"""


from __future__ import annotations

import logging
import re
import traceback
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import List, Optional, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models.organization import Organization
from apps.catalog.models.product import Product
from apps.catalog.models.product_variant import ProductVariant
from apps.catalog.models.packing import Packing
from apps.catalog.models.origin import Origin
from apps.catalog.models.state import State

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_BOOL_TRUE = {"1", "true", "t", "yes", "y"}
_BOOL_FALSE = {"0", "false", "f", "no", "n"}

def _parse_bool(token: str, default: Optional[bool]) -> bool:
    t = token.strip().lower()
    if t == "" and default is not None:
        return default
    if t in _BOOL_TRUE:
        return True
    if t in _BOOL_FALSE:
        return False
    raise ValueError(f"Invalid boolean value: '{token}' (expected one of {sorted(_BOOL_TRUE|_BOOL_FALSE)})")

_decimal_cleaner = re.compile(r"[^\d\.\-]+")

def _parse_decimal(token: str, default: Decimal) -> Decimal:
    t = token.strip()
    if t == "":
        return default
    # allow "1,234.56" or "1234,56" → just strip grouping and normalize comma
    cleaned = _decimal_cleaner.sub("", t.replace(",", "."))
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"Invalid decimal value: '{token}'") from e

def _read_lines_file(path: Path) -> List[str]:
    lines: List[str] = []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            lines.append(line)
    return lines

def parse_items(raw: str) -> List[Tuple[int, int, str, str, int, str, str, int, Decimal, Optional[bool]]]:
    """
    Parse colon-delimited product variant items.

    Format per item (10 fields, latter ones optional):
      org_code:product_id:sku[:barcode][:packing_code][:origin_code][:state_code][:customs_code][:weight][:active]

    Defaults (if omitted):
      packing_code = 2
      origin_code  = 'E'   (assuming you seeded Origin with 'E:EU')
      state_code   = 'A'   (assuming you seeded State  with 'A:Active')
      customs_code = 0
      weight       = 0
      active       = True

    Returns list of tuples:
      (org_code, product_id, sku, barcode, packing_code, origin_code, state_code, customs_code, weight, active_or_None)
    """
    items: List[Tuple[int, int, str, str, int, str, str, int, Decimal, Optional[bool]]] = []
    if not raw:
        return items

    for chunk in raw.split(","):
        part = chunk.strip()
        if not part:
            continue

        bits = part.split(":", 9)  # up to 10 parts
        if len(bits) < 3:
            raise ValueError(
                "Invalid item '{}'. Use: org:product_id:sku[:barcode][:packing][:origin][:state][:customs][:weight][:active]".format(
                    part
                )
            )

        org_str, product_str, sku = bits[0].strip(), bits[1].strip(), bits[2].strip()
        if not org_str or not product_str or not sku:
            raise ValueError(f"Missing required field in '{part}' (need org, product_id, sku).")

        barcode = bits[3].strip() if len(bits) >= 4 else ""
        packing_str = bits[4].strip() if len(bits) >= 5 else ""
        origin_code = (bits[5].strip() if len(bits) >= 6 else "") or "E"
        state_code = (bits[6].strip() if len(bits) >= 7 else "") or "A"
        customs_str = bits[7].strip() if len(bits) >= 8 else ""
        weight_str = bits[8].strip() if len(bits) >= 9 else ""
        active_tok = bits[9].strip() if len(bits) >= 10 else ""

        org_code = int(org_str)
        product_id = int(product_str)
        packing_code = int(packing_str) if packing_str != "" else 2
        customs_code = int(customs_str) if customs_str != "" else 0
        weight = _parse_decimal(weight_str, Decimal("0"))
        active_val = None
        if active_tok != "":
            active_val = _parse_bool(active_tok, default=None)

        # sanity lengths per model
        if len(sku) > 120:
            raise ValueError(f"sku too long ({len(sku)}). Max is 120.")
        if barcode and len(barcode) > 64:
            raise ValueError(f"barcode too long ({len(barcode)}). Max is 64.")
        if len(origin_code) != 1:
            raise ValueError("origin_code must be exactly 1 character.")
        if len(state_code) != 1:
            raise ValueError("state_code must be exactly 1 character.")

        items.append((org_code, product_id, sku, barcode, packing_code, origin_code, state_code, customs_code, weight, active_val))
    return items

# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    """
    Upsert ProductVariant rows.

    Upsert keys (in order):
      1) (organization, sku)
      2) (organization, product, packing_code, origin_code, state_code)
    """

    help = """Upsert product variants (SKUs) from colon-delimited items or a file.
Format per item:
  org:product_id:sku[:barcode][:packing][:origin][:state][:customs][:weight][:active]
Defaults if omitted: packing=2, origin='E', state='A', customs=0, weight=0, active=True

Examples:
  --items "1:1001:SKU-123:4006381333931:2:E:A:0:0.250:1,1:1001:SKU-124:::::0:0.100:"
  --file scripts/variants.txt

Notes:
  • Validates references: Organization(org_code), Product(id), Packing(org+code), Origin(code), State(code).
  • Idempotent upsert: first by (org, sku), then by (org, product, packing, origin, state).
"""

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--items",
            type=str,
            default="",
            help="Comma-separated entries 'org:product_id:sku[:barcode][:packing][:origin][:state][:customs][:weight][:active]'.",
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
                    "Format: org:product_id:sku[:barcode][:packing][:origin][:state][:customs][:weight][:active]"
                )

            # parse once
            parsed = parse_items(",".join(raw_lines))

            created = 0
            updated = 0

            for (org_code, product_id, sku, barcode, packing_code, origin_code, state_code, customs_code, weight, active_val) in parsed:
                # Resolve Organization
                try:
                    org = Organization.objects.get(org_code=org_code)
                except Organization.DoesNotExist:
                    raise CommandError(f"Organization with org_code={org_code} does not exist.")

                # Resolve Product (also sanity-check org if desired)
                try:
                    prod = Product.objects.get(pk=product_id)
                except Product.DoesNotExist:
                    raise CommandError(f"Product with id={product_id} does not exist.")

                # Optional: cross-guard org match (if you enforce product belongs to same org)
                if getattr(prod, "organization_id", None) != org.org_code:
                    raise CommandError(
                        f"Product(id={product_id}) belongs to org={getattr(prod, 'organization_id', None)}, not org={org_code}."
                    )

                # Validate reference codes (packing, origin, state)
                # Packing is per org
                if not Packing.objects.filter(organization=org, packing_code=packing_code).exists():
                    raise CommandError(f"Packing(org={org_code}, code={packing_code}) does not exist.")
                # Origin / State are global (code PK)
                if not Origin.objects.filter(pk=origin_code).exists():
                    raise CommandError(f"Origin(code='{origin_code}') does not exist.")
                if not State.objects.filter(pk=state_code).exists():
                    raise CommandError(f"State(code='{state_code}') does not exist.")

                # Dry run output
                if dry_run:
                    self.stdout.write(
                        f"[DRY] would upsert org={org_code}, product_id={product_id}, sku='{sku}', "
                        f"barcode='{barcode}', packing={packing_code}, origin='{origin_code}', state='{state_code}', "
                        f"customs={customs_code}, weight={weight}, active={active_val if active_val is not None else True}"
                    )
                    continue

                # 1) Try by (org, sku)
                obj: Optional[ProductVariant] = ProductVariant.objects.filter(
                    organization=org, sku=sku
                ).first()

                # 2) Else try by business key (org, product, packing, origin, state)
                if obj is None:
                    obj = ProductVariant.objects.filter(
                        organization=org,
                        product=prod,
                        packing_code=packing_code,
                        origin_code=origin_code,
                        state_code=state_code,
                    ).first()

                    # If found by business key, ensure (org, sku) uniqueness will not be violated
                    if obj is not None and obj.sku != sku:
                        conflict = ProductVariant.objects.filter(organization=org, sku=sku).exclude(pk=obj.pk).exists()
                        if conflict:
                            raise CommandError(
                                f"Conflict: another variant with org={org_code} already has sku='{sku}'."
                            )
                        obj.sku = sku  # allow sku update on the found business-key row

                # Prepare defaults/updates
                is_active = active_val if active_val is not None else True

                if obj is None:
                    obj = ProductVariant.objects.create(
                        organization=org,
                        product=prod,
                        sku=sku,
                        barcode=(barcode or None),
                        packing_code=packing_code,
                        origin_code=origin_code,
                        state_code=state_code,
                        customs_code=customs_code,
                        weight=weight,
                        is_active=is_active,
                    )
                    created += 1
                    self.stdout.write(
                        f"Created variant id={obj.id} org={org_code} sku='{obj.sku}' (product_id={product_id})"
                    )
                else:
                    # update fields
                    obj.product = prod
                    obj.barcode = (barcode or None)
                    obj.packing_code = packing_code
                    obj.origin_code = origin_code
                    obj.state_code = state_code
                    obj.customs_code = customs_code
                    obj.weight = weight
                    obj.is_active = is_active
                    obj.save(
                        update_fields=[
                            "product",
                            "sku",            # may have been adjusted above
                            "barcode",
                            "packing_code",
                            "origin_code",
                            "state_code",
                            "customs_code",
                            "weight",
                            "is_active",
                        ]
                    )
                    updated += 1
                    self.stdout.write(
                        f"Updated variant id={obj.id} org={org_code} sku='{obj.sku}' (product_id={product_id})"
                    )

            if dry_run:
                self.stdout.write(self.style.SUCCESS("Dry run complete. No changes applied."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}."))

        except Exception as e:
            tb = traceback.format_exc()
            logger.warning(f"Seed product variants failed: {e}")
            # Always include traceback per project rules
            raise CommandError(f"Error seeding product variants: {e}\n{tb}")

