# apps/catalog/services/product_ops.py

# apps/catalog/services/product_ops.py
"""
Purpose:
    Service layer for managing Product records. Provides a transactional,
    idempotent upsert function that enforces business keys and validates
    references to related entities.

Context:
    A Product represents a catalog entry tied to an Organization,
    Manufacturer, and optionally a ProductGroup. This service is designed
    to be used by import pipelines, admin features, or API endpoints to
    safely create or update product records.

Used by:
    - Seeding commands for products.
    - Import/ETL jobs that sync manufacturer data into the catalog.
    - Admin operations and APIs that create/update product definitions.

Depends on:
    - apps.core.models.Organization
    - apps.catalog.models.Manufacturer
    - apps.catalog.models.ProductGroup
    - apps.catalog.models.Product

Key Features:
    - Atomic upsert by (organization, manufacturer, manufacturer_part_number, slug).
    - Resolves foreign keys (Organization, Manufacturer, ProductGroup).
    - Enforces required fields: org_code, manufacturer_code,
      manufacturer_part_number, name, slug.
    - Optional fields: product_group_code, is_active.
    - Raises ValidationError for missing required fields.

Example:
    >>> from apps.catalog.services.product_ops import upsert_product
    >>> payload = {
    ...     "org_code": 1,
    ...     "manufacturer_code": 10,
    ...     "manufacturer_part_number": "ZX-9",
    ...     "name": "Widget ZX-9",
    ...     "slug": "widget-zx-9",
    ...     "product_group_code": "GRP01",
    ...     "is_active": True,
    ... }
    >>> p, created = upsert_product(payload)
    >>> print(p.id, created)
"""

from __future__ import annotations

from typing import Dict, Tuple, Optional
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.core.models.organization import Organization
from apps.catalog.models.product import Product
from apps.catalog.models.manufacturer import Manufacturer
from apps.catalog.models.product_group import ProductGroup


def _get_product_group(org_code: int, product_group_code: Optional[str]) -> Optional[ProductGroup]:
    if not product_group_code:
        return None
    org = Organization.objects.get(org_code=org_code)
    return ProductGroup.objects.get(organization=org, product_group_code=product_group_code)


@transaction.atomic
def upsert_product(payload: Dict) -> Tuple[Product, bool]:
    """
    Upsert a Product via dict.

    Required: org_code, manufacturer_code, manufacturer_part_number, name, slug
    Optional: product_group_code, is_active (bool)

    Returns: (product, created)
    Raises: ValidationError, DoesNotExist, IntegrityError
    """
    required = ["org_code", "manufacturer_code", "manufacturer_part_number", "name", "slug"]
    missing = [k for k in required if payload.get(k) in (None, "")]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    org = Organization.objects.get(org_code=payload["org_code"])
    manu = Manufacturer.objects.get(manufacturer_code=payload["manufacturer_code"])
    pg = _get_product_group(payload["org_code"], payload.get("product_group_code"))

    defaults = {
        "name": payload["name"],
        "is_active": bool(payload.get("is_active", True)),
        "product_group": pg,
    }

    # Selector entspricht deinen Uniques: wir nehmen (org, manufacturer, mpn, slug)
    # → robust gegen erneute Aufrufe; DB schützt via Uniques zusätzlich.
    obj, created = Product.objects.update_or_create(
        organization=org,
        manufacturer=manu,
        manufacturer_part_number=payload["manufacturer_part_number"],
        slug=payload["slug"],
        defaults=defaults,
    )
    return obj, created
#
# from apps.catalog.services.product_ops import upsert_product
#
# p, created = upsert_product({
#     "org_code": 1,
#     "manufacturer_code": 10,
#     "manufacturer_part_number": "ZX-9",
#     "name": "Widget ZX-9",
#     "slug": "widget-zx-9",
#     "product_group_code": "GRP01",
#     "is_active": True,
# })
# print(p.id, created)
#
#     payload = {
#         "org_code": 1,
#         "manufacturer_code": 1,
#         "manufacturer_part_number": "ZX-9",
#         "name": "Widget ZX-9",
#         "slug": "widget-zx-9",
#         "product_group_code": "1",
#         "is_active": True,
#     }
#
#     p, created = upsert_product(payload)
#     print(f"Product: {p}, created={created}")