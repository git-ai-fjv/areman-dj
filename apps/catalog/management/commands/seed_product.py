# apps/catalog/management/commands/seed_product.py

# apps/catalog/management/commands/seed_product.py
"""
Purpose:
    Management command to upsert Product records into the catalog.
    Accepts colon-delimited items or a file, resolving Organization,
    Manufacturer, and optional ProductGroup. Ensures products are
    uniquely identified by either slug or normalized manufacturer
    part number.

Context:
    Part of the catalog seeding workflow. Used during system setup
    and migrations to preload or update product master data across
    organizations. Ensures consistent slug generation and idempotent
    product creation.

Used by:
    - Administrators to seed or bulk-update products.
    - Import/ETL pipelines when syncing product data from ERP or supplier feeds.
    - Developers to quickly populate test data during local development.

Depends on:
    - apps.core.models.organization.Organization (organization resolution).
    - apps.catalog.models.manufacturer.Manufacturer (required foreign key).
    - apps.catalog.models.product_group.ProductGroup (optional grouping).
    - apps.catalog.models.product.Product (target table).
    - Utility functions for slug normalization and uniqueness.

Key Features:
    - Parses flexible colon-delimited format:
      org_code:manufacturer_code:mpn[:name][:slug][:product_group_code][:active]
    - Auto-generates slug if omitted, enforcing uniqueness per organization.
    - Normalizes MPNs for fallback matching (lowercased, umlaut replacements, non-alnum stripped).
    - Supports dry-run mode for safe validation.
    - Uses atomic transactions for batch safety.

Examples:
    # Dry run with explicit slug
    python manage.py seed_product --items "1:10:ZX-9:Widget ZX-9:widget-zx-9:GRP01:1" --dry-run

    # Apply simple records with and without group/slug
    python manage.py seed_product --items "1:10:ZX-9:Widget ZX-9:::1,1:10:MPN-123::::0"

    # Load from file
    python manage.py seed_product --file scripts/products.txt
"""


# example:
# python manage.py seed_product --items "1:10:ZX-9:Widget ZX-9:widget-zx-9:GRP01:1,1:10:MPN-123::::GRP01:0,1:11:ABC-42:Cool Part::GRP02:"

from __future__ import annotations

import logging
import re
import traceback
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models.organization import Organization
from apps.catalog.models.manufacturer import Manufacturer
from apps.catalog.models.product_group import ProductGroup
from apps.catalog.models.product import Product

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Parsing
# ------------------------------------------------------------------------------

def _parse_bool(token: str) -> bool:
    t = token.strip().lower()
    return t in {"1", "true", "t", "yes", "y"}

def _read_items_file(path: Path) -> List[str]:
    lines: List[str] = []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            lines.append(line)
    return lines

def parse_items(raw: str) -> List[Tuple[int, int, str, str, str, str, Optional[bool]]]:
    """
    Parse products from a compact, colon-delimited format.

    Format per item (7 fields, fields 4..7 optional):
        org_code:manufacturer_code:mpn[:name][:slug][:product_group_code][:active]

    Examples:
        "1:10:ZX-9:Widget ZX-9:widget-zx-9:GRP01:1"
        "1:10:MPN-123::::0"              # only org, manu, mpn, active=false
        "2:5:ABC-42:Cool Part:::"         # missing slug/group/active → auto slug, no group, active=True

    Returns list of tuples:
        (org_code, manufacturer_code, mpn, name, slug, product_group_code, active_or_None)
    """
    items: List[Tuple[int, int, str, str, str, str, Optional[bool]]] = []
    if not raw:
        return items

    for chunk in raw.split(","):
        part = chunk.strip()
        if not part:
            continue

        bits = part.split(":", 6)  # up to 7 segments
        if len(bits) < 3:
            raise ValueError(
                f"Invalid item '{part}'. Use 'org:manufacturer_code:mpn[:name][:slug][:product_group_code][:active]'"
            )

        org_str, manu_str, mpn = bits[0].strip(), bits[1].strip(), bits[2].strip()
        name = bits[3].strip() if len(bits) >= 4 else ""
        slug = bits[4].strip() if len(bits) >= 5 else ""
        group_code = bits[5].strip() if len(bits) >= 6 else ""
        active_tok = bits[6].strip() if len(bits) >= 7 else ""

        if not org_str or not manu_str or not mpn:
            raise ValueError(f"Missing required field in '{part}' (need org, manufacturer_code, mpn).")

        org_code = int(org_str)
        manufacturer_code = int(manu_str)
        is_active = _parse_bool(active_tok) if active_tok != "" else None

        # hard caps similar to model constraints
        if len(name) > 200:
            name = name[:200]
        if len(slug) > 200:
            slug = slug[:200]
        if len(mpn) > 100:
            mpn = mpn[:100]
        if len(group_code) > 20:
            group_code = group_code[:20]

        items.append((org_code, manufacturer_code, mpn, name, slug, group_code, is_active))
    return items

# ------------------------------------------------------------------------------
# Normalization helpers (mirror DB logic)
# ------------------------------------------------------------------------------

_UMLAUT_MAP = (
    ("ß", "ss"),
    ("ẞ", "ss"),
    ("ä", "ae"),
    ("ö", "oe"),
    ("ü", "ue"),
)

_NON_ALNUM_LOWER = re.compile(r"[^0-9a-z]+")

def normalize_mpn(mpn: str) -> str:
    s = mpn.lower()
    for a, b in _UMLAUT_MAP:
        s = s.replace(a, b)
    s = _NON_ALNUM_LOWER.sub("", s)
    return s

_SLUG_NON_ALNUM = re.compile(r"[^0-9a-z]+")

def _simple_slugify(text: str) -> str:
    s = text.lower()
    s = _SLUG_NON_ALNUM.sub("-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s[:200] if len(s) > 200 else s

def _unique_slug_for_org(org: Organization, desired: str, exclude_id: Optional[int] = None) -> str:
    base = desired or "product"
    slug = base
    i = 2
    while True:
        qs = Product.objects.filter(organization=org, slug=slug)
        if exclude_id is not None:
            qs = qs.exclude(pk=exclude_id)
        if not qs.exists():
            return slug
        slug = f"{base}-{i}"
        i += 1

# ------------------------------------------------------------------------------
# Command
# ------------------------------------------------------------------------------

class Command(BaseCommand):
    """
    Upsert Products by either (organization, slug) or (organization, manufacturer, manufacturer_part_number_norm).
    If slug is omitted, we auto-generate a unique slug based on name or "<manufacturer_code>-<mpn>".

    Usage:
      python manage.py seed_product --items "1:10:ZX-9:Widget ZX-9:widget-zx-9:GRP01:1,1:10:MPN-123::::0"
      python manage.py seed_product --file scripts/products.txt
      python manage.py seed_product --items "1:10:ZX-9:Widget ZX-9::::" --dry-run
    """

    help = """Upsert products from simple colon-delimited items or a file.
    Format per item: org:manufacturer_code:mpn[:name][:slug][:product_group_code][:active]
    Examples:
      --items "1:10:ZX-9:Widget ZX-9:widget-zx-9:GRP01:1,1:10:MPN-123::::GRP01:0,1:11:ABC-42:Cool Part::GRP02:"
    If slug is omitted, it will be generated. product_group_code is optional.
    """

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--items",
            type=str,
            default="",
            help="Comma-separated entries 'org:manufacturer_code:mpn[:name][:slug][:product_group_code][:active]'.",
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
            raw_chunks: List[str] = []
            if items_arg:
                raw_chunks.extend([p.strip() for p in items_arg.split(",") if p.strip()])
            if file_arg:
                raw_chunks.extend(_read_items_file(Path(file_arg)))

            if not raw_chunks:
                raise CommandError(
                    "No items provided. Use --items or --file. "
                    "Format: org:manufacturer_code:mpn[:name][:slug][:product_group_code][:active]"
                )

            # Parse
            parsed: List[Tuple[int, int, str, str, str, str, Optional[bool]]] = []
            parsed.extend(parse_items(",".join(raw_chunks)))

            created = 0
            updated = 0

            for (org_code, manu_code, mpn, name, slug, group_code, active_val) in parsed:
                # Resolve Organization
                try:
                    org = Organization.objects.get(org_code=org_code)
                except Organization.DoesNotExist:
                    raise CommandError(f"Organization org_code={org_code} does not exist.")

                # Resolve Manufacturer
                try:
                    manu = Manufacturer.objects.get(manufacturer_code=manu_code)
                except Manufacturer.DoesNotExist:
                    raise CommandError(f"Manufacturer manufacturer_code={manu_code} does not exist.")

                # Resolve ProductGroup (optional)
                pg_obj: Optional[ProductGroup] = None
                if group_code:
                    try:
                        pg_obj = ProductGroup.objects.get(
                            organization=org, item_group_code=group_code
                        )
                    except ProductGroup.DoesNotExist:
                        raise CommandError(
                            f"ProductGroup with org_code={org_code} and item_group_code='{group_code}' does not exist."
                        )

                # Determine upsert key
                target_slug = slug.strip()
                if not target_slug:
                    base_for_slug = name.strip() or f"{manu_code}-{mpn}"
                    target_slug = _simple_slugify(base_for_slug)

                if dry_run:
                    self.stdout.write(
                        f"[DRY] would upsert org={org_code}, manu={manu_code}, mpn='{mpn}', "
                        f"name='{name}', slug='{target_slug}', group='{group_code or ''}', "
                        f"active={active_val if active_val is not None else True}"
                    )
                    continue

                # Try find by slug first
                obj: Optional[Product] = Product.objects.filter(
                    organization=org, slug=target_slug
                ).first()

                # If not found by slug, try by normalized MPN + manufacturer within org
                if obj is None:
                    mpn_norm = normalize_mpn(mpn)
                    obj = (
                        Product.objects.filter(
                            organization=org,
                            manufacturer=manu,
                            manufacturer_part_number_norm=mpn_norm,
                        )
                        .order_by("id")
                        .first()
                    )

                # Prepare fields
                fields = {
                    "organization": org,
                    "manufacturer": manu,
                    "manufacturer_part_number": mpn,
                    "name": name or (obj.name if obj else f"{manu_code} {mpn}"),
                    "is_active": active_val if active_val is not None else True,
                    "product_group": pg_obj,
                }

                if obj is None:
                    # ensure unique slug for org
                    unique_slug = _unique_slug_for_org(org, target_slug)
                    obj = Product(slug=unique_slug, **fields)
                    obj.save()
                    created += 1
                    self.stdout.write(
                        f"Created product id={obj.id} org={org_code} slug='{obj.slug}' (manu={manu_code}, mpn='{mpn}')"
                    )
                else:
                    # if slug differs or conflicts, pick a unique one
                    desired_slug = target_slug
                    if obj.slug != desired_slug:
                        desired_slug = _unique_slug_for_org(org, desired_slug, exclude_id=obj.id)
                        obj.slug = desired_slug

                    # update other fields
                    obj.manufacturer = manu
                    obj.manufacturer_part_number = mpn
                    obj.name = fields["name"]
                    obj.is_active = fields["is_active"]
                    obj.product_group = pg_obj
                    obj.save(update_fields=["slug", "manufacturer", "manufacturer_part_number", "name", "is_active", "product_group"])
                    updated += 1
                    self.stdout.write(
                        f"Updated product id={obj.id} org={org_code} slug='{obj.slug}'"
                    )

            if dry_run:
                self.stdout.write(self.style.SUCCESS("Dry run complete. No changes applied."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}."))

        except Exception as e:
            tb = traceback.format_exc()
            logger.warning(f"Seed products failed: {e}")
            raise CommandError(f"Error seeding products: {e}\n{tb}")
