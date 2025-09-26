# apps/procurement/services/supplier_product_ops.py
"""
Purpose:
    Provides operations to safely insert or update SupplierProduct records.
    Ensures consistent links between Organization, Supplier, and ProductVariant.

Context:
    Part of the `apps.procurement` app. Encapsulates business logic for
    managing supplier-specific product definitions.

Used by:
    - Import pipelines that load supplier catalog data
    - Procurement services that need to attach variants to suppliers
    - Synchronization jobs for maintaining supplier SKU references

Depends on:
    - apps.core.models.Organization
    - apps.partners.models.Supplier
    - apps.catalog.models.ProductVariant
    - apps.procurement.models.SupplierProduct
    - Django transaction management

Example:
    from apps.procurement.services.supplier_product_ops import upsert_supplier_product

    payload = {
        "org_code": 1,
        "supplier_id": 42,
        "variant_id": 99,
        "supplier_sku": "SUP-ART-2025",
        "pack_size": 10,
        "min_order_qty": 100,
        "lead_time_days": 14,
        "is_active": True,
        "supplier_description": "10mm Steel Bolts",
        "notes": "Special pricing valid until 2025-12-31",
    }
    sp, created = upsert_supplier_product(payload)
    print(sp.id, created)
"""


from __future__ import annotations

from typing import Dict, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.core.models.organization import Organization
from apps.partners.models.supplier import Supplier
from apps.catalog.models.product_variant import ProductVariant
from apps.procurement.models.supplier_product import SupplierProduct


@transaction.atomic
def upsert_supplier_product(payload: Dict) -> Tuple[SupplierProduct, bool]:
    """
    Upsert a SupplierProduct via dict.

    Required:
        org_code, supplier_id, variant_id, supplier_sku
    Optional:
        pack_size, min_order_qty, lead_time_days,
        is_active, supplier_description, notes

    Returns:
        (supplier_product, created)
    Raises:
        ValidationError, DoesNotExist, IntegrityError
    """
    required = ["org_code", "supplier_id", "variant_id", "supplier_sku"]
    missing = [k for k in required if payload.get(k) in (None, "")]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    org = Organization.objects.get(org_code=int(payload["org_code"]))
    supplier = Supplier.objects.get(id=int(payload["supplier_id"]))
    variant = ProductVariant.objects.get(id=int(payload["variant_id"]))

    defaults = {
        "supplier_sku": payload["supplier_sku"],
        "pack_size": payload.get("pack_size", 1),
        "min_order_qty": payload.get("min_order_qty", 0),
        "lead_time_days": payload.get("lead_time_days", 0),
        "is_active": bool(payload.get("is_active", True)),
        "supplier_description": payload.get("supplier_description", ""),
        "notes": payload.get("notes"),
    }

    obj, created = SupplierProduct.objects.update_or_create(
        organization=org,
        supplier=supplier,
        variant=variant,
        defaults=defaults,
    )
    return obj, created


# from decimal import Decimal
# from apps.procurement.services.supplier_product_ops import upsert_supplier_product
#
# payload = {
#     "org_code": 1,
#     "supplier_id": 42,
#     "variant_id": 99,
#     "supplier_sku": "SUP-ART-2025",
#     "pack_size": Decimal("10.0"),
#     "min_order_qty": Decimal("100.0"),
#     "lead_time_days": 14,
#     "is_active": True,
#     "supplier_description": "10mm Steel Bolts",
#     "notes": "Special pricing agreed until 2025-12-31",
# }
#
# sp, created = upsert_supplier_product(payload)
# print(f"SupplierProduct: {sp}, created={created}")

