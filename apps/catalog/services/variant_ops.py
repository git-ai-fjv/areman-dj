# apps/catalog/services/variant_ops.py
"""
Purpose:
    Service layer for managing ProductVariant records. Provides a transactional,
    idempotent upsert function that supports both SKU-based and business-key–
    based selectors for flexible variant creation and updates.

Context:
    A ProductVariant (SKU) represents a specific sellable unit of a Product.
    Variants may differ by packing, origin, state, customs code, or barcode.
    This service abstracts the variant creation/update logic to enforce
    consistent handling across imports, admin features, and APIs.

Used by:
    - Import/ETL pipelines that generate or update SKUs.
    - Seeding scripts for initial data population.
    - Business logic that maintains catalog consistency.

Depends on:
    - apps.core.models.Organization
    - apps.catalog.models.Product
    - apps.catalog.models.ProductVariant
    - apps.catalog.models.Packing
    - apps.catalog.models.Origin
    - apps.catalog.models.State

Key Features:
    - Required fields: org_code, product_id.
    - Preferred selector: (org, sku).
    - Alternative selector: (org, product, packing, origin, state).
    - Generates a fallback SKU when not provided.
    - Resolves references to Packing, Origin, and State if codes are supplied.
    - Atomic transaction guarantees idempotency and consistency.
    - Raises ValidationError for missing required fields.

Example:
    >>> from apps.catalog.services.variant_ops import upsert_variant
    >>> payload = {
    ...     "org_code": 1,
    ...     "product_id": 1001,
    ...     "sku": "SKU-123",
    ...     "barcode": "4006381333931",
    ...     "packing_code": 2,
    ...     "origin_code": "E",
    ...     "state_code": "A",
    ...     "customs_code": 0,
    ...     "weight": "0.250",
    ...     "is_active": True,
    ... }
    >>> v, created = upsert_variant(payload)
    >>> print(v.id, created)
"""


from __future__ import annotations

from decimal import Decimal
from typing import Dict, Tuple, Optional
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.core.models.organization import Organization
from apps.catalog.models.product import Product
from apps.catalog.models.product_variant import ProductVariant
from apps.catalog.models.packing import Packing
from apps.catalog.models.origin import Origin
from apps.catalog.models.state import State


def _as_decimal(value, default: Decimal) -> Decimal:
    if value is None or value == "":
        return default
    return Decimal(str(value))


@transaction.atomic
def upsert_variant(payload: Dict) -> Tuple[ProductVariant, bool]:
    """
    Upsert a ProductVariant via dict.

    Required: org_code, product_id
    Selector:
      - preferred via (org_code, sku) if 'sku' provided
      - otherwise via Business-Key (org_code, product, packing, origin, state)

    Optional fields: barcode, customs_code, weight, is_active,
                     packing_code, origin_code, state_code
    Returns: (variant, created)
    Raises: ValidationError, DoesNotExist, IntegrityError
    """
    required = ["org_code", "product_id"]
    missing = [k for k in required if payload.get(k) in (None, "")]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    org = Organization.objects.get(org_code=payload["org_code"])
    product = Product.objects.get(id=payload["product_id"])

    # Resolve foreign keys
    packing: Optional[Packing] = None
    if payload.get("packing_code"):
        packing = Packing.objects.get(organization=org, packing_code=payload["packing_code"])

    origin: Optional[Origin] = None
    if payload.get("origin_code"):
        origin = Origin.objects.get(origin_code=payload["origin_code"])

    state: Optional[State] = None
    if payload.get("state_code"):
        state = State.objects.get(state_code=payload["state_code"])

    sku: Optional[str] = payload.get("sku")

    defaults = {
        "barcode": payload.get("barcode") or None,
        "customs_code": int(payload.get("customs_code", 0)),
        "weight": _as_decimal(payload.get("weight"), Decimal("0")),
        "is_active": bool(payload.get("is_active", True)),
        "packing": packing,
        "origin": origin,
        "state": state,
        "product": product,
        "organization": org,
    }

    if sku:
        obj, created = ProductVariant.objects.update_or_create(
            organization=org,
            sku=sku,
            defaults=defaults,
        )
    else:
        # Business-Key: (org, product, packing, origin, state)
        obj, created = ProductVariant.objects.update_or_create(
            organization=org,
            product=product,
            packing=packing,
            origin=origin,
            state=state,
            defaults={
                **defaults,
                "sku": payload.get("generated_sku")
                or f"{product.id}-{packing and packing.packing_code}-{origin and origin.origin_code}-{state and state.state_code}",
            },
        )
    return obj, created
