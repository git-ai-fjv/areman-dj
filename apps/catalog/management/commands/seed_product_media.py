# apps/catalog/management/commands/seed_product_media.py
# Created according to the user's Copilot Base Instructions.
from __future__ import annotations

import logging
import traceback
from pathlib import Path
from typing import List, Optional, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models.organization import Organization
from apps.catalog.models.product import Product
from apps.catalog.models.product_variant import ProductVariant
from apps.catalog.models.product_media import ProductMedia

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


def _to_int_or_none(token: str) -> Optional[int]:
    s = (token or "").strip()
    if s == "":
        return None
    try:
        return int(s)
    except ValueError:
        raise ValueError(f"Invalid integer value: '{token}'")


def _read_lines_file(path: Path) -> List[str]:
    out: List[str] = []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            out.append(line)
    return out


def parse_items(raw: str) -> List[
    Tuple[int, str, str, str, int, str, Optional[str], Optional[str], Optional[int], Optional[int], Optional[int], Optional[bool]]
]:
    """
    Parse colon-delimited product media entries.

    Per item (up to 12 fields; last 9 optional):
      org:product_ref:media_url[:role][:sort_order][:alt_text][:variant_ref][:mime][:width][:height][:file_size][:active]

    Where:
      - product_ref: product slug (preferred) or numeric product id
      - variant_ref: SKU (preferred) or numeric variant id (optional)
      - role default = 'gallery'
      - sort_order default = 0
      - alt_text default = ''
      - active default = True
      - width/height/file_size integers, optional

    Examples:
      1:widget-a:https://cdn/x.jpg:main:0:Front image
      1:widget-a:https://cdn/y.jpg:gallery:1::SKU-1001:image/jpeg:1200:1200:154000:1
    """
    items: List[
        Tuple[int, str, str, str, int, str, Optional[str], Optional[str], Optional[int], Optional[int], Optional[int], Optional[bool]]
    ] = []
    if not raw:
        return items

    for chunk in raw.split(","):
        part = chunk.strip()
        if not part:
            continue

        bits = part.split(":", 11)  # up to 12 parts
        if len(bits) < 3:
            raise ValueError(
                f"Invalid item '{part}'. "
                "Use 'org:product_ref:media_url[:role][:sort][:alt][:variant_ref][:mime][:width][:height][:file_size][:active]'"
            )

        org_str = bits[0].strip()
        product_ref = (bits[1] or "").strip()
        media_url = (bits[2] or "").strip()

        role = (bits[3].strip() if len(bits) >= 4 and bits[3].strip() else "gallery")
        sort_ord = _to_int_or_none(bits[4]) if len(bits) >= 5 else 0
        sort_order = 0 if sort_ord is None else sort_ord
        alt_text = (bits[5] if len(bits) >= 6 else "") or ""

        variant_ref = (bits[6].strip() if len(bits) >= 7 else "") or None
        mime = (bits[7].strip() if len(bits) >= 8 else "") or None
        width = _to_int_or_none(bits[8]) if len(bits) >= 9 else None
        height = _to_int_or_none(bits[9]) if len(bits) >= 10 else None
        file_size = _to_int_or_none(bits[10]) if len(bits) >= 11 else None
        active_tok = (bits[11].strip() if len(bits) >= 12 else "")

        if not org_str or not product_ref or not media_url:
            raise ValueError(f"Missing org, product_ref or media_url in '{part}'")

        org_code = int(org_str)

        # enforce length limits
        role = role[:20]
        alt_text = alt_text[:200]
        if mime:
            mime = mime[:100]

        active_val = _parse_bool(active_tok, default=True) if active_tok != "" else None

        items.append(
            (org_code, product_ref, media_url, role, sort_order, alt_text, variant_ref, mime, width, height, file_size, active_val)
        )
    return items


# ------------------------------------------------------------------------------
# Command
# ------------------------------------------------------------------------------

class Command(BaseCommand):
    """
    Upsert ProductMedia rows using natural key (organization, product, variant, media_url).
    Variant is optional; when provided we also validate that variant.product == product.
    """

    help = """Upsert product media from colon-delimited items or a file.

Format per item:
  org:product_ref:media_url[:role][:sort_order][:alt_text][:variant_ref][:mime][:width][:height][:file_size][:active]

Defaults: role='gallery', sort_order=0, alt_text='', active=True.

product_ref: product slug or numeric id
variant_ref: SKU or numeric variant id (optional)

Examples:
  --items "1:widget-a:https://cdn/img1.jpg:main:0:Front,1:widget-a:https://cdn/img2.jpg"
  --file scripts/product_media.txt
"""

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--items",
            type=str,
            default="",
            help="Comma-separated entries 'org:product_ref:media_url[:role][:sort][:alt][:variant_ref][:mime][:width][:height][:file_size][:active]'.",
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
                    "Format: org:product_ref:media_url[:role][:sort][:alt][:variant_ref][:mime][:width][:height][:file_size][:active]"
                )

            parsed = parse_items(",".join(raw_lines))

            created = 0
            updated = 0

            for (
                org_code,
                product_ref,
                media_url,
                role,
                sort_order,
                alt_text,
                variant_ref,
                mime,
                width,
                height,
                file_size,
                active_val,
            ) in parsed:
                # Resolve org
                try:
                    org = Organization.objects.get(org_code=org_code)
                except Organization.DoesNotExist:
                    raise CommandError(f"Organization with org_code={org_code} does not exist.")

                # Resolve product: try slug (preferred), then numeric id
                product = Product.objects.filter(organization=org, slug=product_ref).first()
                if product is None and product_ref.isdigit():
                    product = Product.objects.filter(organization=org, id=int(product_ref)).first()
                if product is None:
                    raise CommandError(f"Product '{product_ref}' not found for org={org_code} (by slug or id).")

                # Resolve optional variant: try SKU (preferred), then numeric id
                variant = None
                if variant_ref:
                    variant = ProductVariant.objects.filter(organization=org, sku=variant_ref).first()
                    if variant is None and variant_ref.isdigit():
                        variant = ProductVariant.objects.filter(organization=org, id=int(variant_ref)).first()
                    if variant is None:
                        raise CommandError(
                            f"Variant '{variant_ref}' not found for org={org_code} (by SKU or id)."
                        )
                    # sanity: variant must belong to product
                    if variant.product_id != product.id:
                        raise CommandError(
                            f"Variant '{variant_ref}' (id={variant.id}) does not belong to product id={product.id}."
                        )

                if dry_run:
                    self.stdout.write(
                        f"[DRY] would upsert org={org_code} prod={product.id} "
                        f"var={variant.id if variant else '—'} url='{media_url}' role={role} sort={sort_order} "
                        f"active={active_val if active_val is not None else True}"
                    )
                    continue

                # Natural key for upsert
                obj, was_created = ProductMedia.objects.update_or_create(
                    organization=org,
                    product=product,
                    variant=variant,
                    media_url=media_url,
                    defaults={
                        "role": role,
                        "sort_order": sort_order,
                        "alt_text": alt_text,
                        "mime": mime,
                        "width_px": width,
                        "height_px": height,
                        "file_size": file_size,
                        "is_active": active_val if active_val is not None else True,
                    },
                )

                if was_created:
                    created += 1
                    self.stdout.write(
                        f"Created product_media id={obj.id} org={org_code} prod={product.id} "
                        f"var={variant.id if variant else '—'}"
                    )
                else:
                    updated += 1
                    self.stdout.write(
                        f"Updated product_media id={obj.id} org={org_code} prod={product.id} "
                        f"var={variant.id if variant else '—'}"
                    )

            if dry_run:
                self.stdout.write(self.style.SUCCESS("Dry run complete. No changes applied."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}."))

        except Exception as e:
            tb = traceback.format_exc()
            logger.warning(f"Seed product media failed: {e}")
            # Always include traceback per project rules
            raise CommandError(f"Error seeding product media: {e}\n{tb}")



