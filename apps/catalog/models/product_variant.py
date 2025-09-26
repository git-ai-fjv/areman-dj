
# apps/catalog/models/product_variant.py
"""
Purpose:
    Defines the ProductVariant entity, which represents a sellable unit (SKU).
    Captures identifiers, logistics data, order constraints, availability,
    and marketing attributes that extend the base Product.

Context:
    Belongs to the `catalog` app. Each ProductVariant links a Product with
    its Packing, Origin, and State. Variants are the concrete SKUs used for
    procurement, pricing, stock, and sales channel operations.

Fields:
    - organization (FK → core.Organization): Owning organization (multi-tenant scope).
    - product (FK → catalog.Product): The base product this variant belongs to.
    - packing (FK → catalog.Packing): Packaging unit of this variant.
    - origin (FK → catalog.Origin): Origin classification code.
    - state (FK → catalog.State): State classification code.
    - sku (CharField, 120): Internal stock-keeping unit identifier.
    - ean (CharField, 14): Standardized GTIN/EAN code (optional, indexed).
    - barcode (CharField, 64): Non-standard or supplier barcode (optional).
    - customs_code (IntegerField): Customs tariff number (optional).
    - weight / width / height / length (DecimalField): Logistics dimensions.
    - eclass_code (CharField, 16): International eCl@ss classification (optional).
    - stock_quantity / available_stock (IntegerField): Stock and availability data.
    - is_available (BooleanField): Availability flag from supplier API.
    - shipping_free (BooleanField): Free shipping flag.
    - min_purchase / max_purchase / purchase_steps (IntegerField): Order constraints.
    - is_topseller (BooleanField): Marketing flag for top seller status.
    - is_active (BooleanField): Whether this variant is active.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Organization → multiple ProductVariants
    - Product → multiple ProductVariants
    - Packing → multiple ProductVariants
    - Origin → multiple ProductVariants
    - State → multiple ProductVariants
    - ProductVariant ↔ ChannelVariant (publish variants to channels)
    - ProductVariant ↔ SupplierProduct (procurement linkage)

Used by:
    - apps.catalog.models.Product
    - apps.catalog.models.ChannelVariant
    - apps.procurement.models.SupplierProduct
    - apps.pricing.models.SalesChannelVariantPrice

Depends on:
    - core.Organization
    - catalog.Product
    - catalog.Packing
    - catalog.Origin
    - catalog.State

Example:
    >>> from apps.catalog.models import ProductVariant
    >>> pv = ProductVariant.objects.create(
    ...     organization=org,
    ...     product=prod,
    ...     packing=pack,
    ...     origin=orig,
    ...     state=state,
    ...     sku="SKU-123",
    ...     ean="4006381333931",
    ...     weight="1.250",
    ... )
    >>> print(pv)
    [org=1] SKU=SKU-123 (product_id=42)
"""



from __future__ import annotations

from django.db import models
from django.db.models import CheckConstraint, Q
from django.db.models.functions import Now


class ProductVariant(models.Model):
    """
    Sellable unit (SKU). Holds SKU/EAN, packaging, logistics data,
    order constraints, availability, and marketing flags.
    """

    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
        related_name="product_variants",
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="product_variants",
    )
    packing = models.ForeignKey(
        "catalog.Packing",
        on_delete=models.PROTECT,
        related_name="product_variants",
    )
    origin = models.ForeignKey(
        "catalog.Origin",
        on_delete=models.PROTECT,
        related_name="product_variants",
    )
    state = models.ForeignKey(
        "catalog.State",
        on_delete=models.PROTECT,
        related_name="product_variants",
    )

    # Identity & scanning
    sku = models.CharField(max_length=120)
    ean = models.CharField(
        max_length=14,
        null=True,
        blank=True,
        db_index=True,
        help_text="Standardized GTIN/EAN code (8, 12, 13, or 14 digits).",
    )
    barcode = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="Non-standard or supplier-specific barcode (may be alphanumeric).",
    )

    # Logistics & classification
    customs_code = models.IntegerField(null=True, blank=True)
    weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    width = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    height = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    length = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)

    eclass_code = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        help_text="International eCl@ss classification code (e.g. 44070702).",
    )

    # Stock & availability
    stock_quantity = models.IntegerField(null=True, blank=True)
    available_stock = models.IntegerField(null=True, blank=True)
    is_available = models.BooleanField(
        default=False,
        help_text="Availability flag as provided by supplier API.",
    )
    shipping_free = models.BooleanField(default=False)

    # Order constraints
    min_purchase = models.IntegerField(default=1)
    max_purchase = models.IntegerField(null=True, blank=True)
    purchase_steps = models.IntegerField(default=1)

    # Marketing
    is_topseller = models.BooleanField(
        default=False,
        help_text="Flag indicating this variant is marked as top seller in the shop.",
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"[org={self.organization}] SKU={self.sku} (product_id={self.product_id})"

    class Meta:
        constraints = [
            CheckConstraint(check=Q(weight__gte=0), name="ck_variant_weight_nonneg"),
            models.UniqueConstraint(fields=("organization", "sku"), name="uniq_variant_org_sku"),
            models.UniqueConstraint(fields=("organization", "id"), name="uniq_variant_org_id"),
            models.UniqueConstraint(
                fields=("organization", "product", "packing", "origin", "state"),
                name="uniq_variant_org_product_pack_origin_state",
            ),
        ]
