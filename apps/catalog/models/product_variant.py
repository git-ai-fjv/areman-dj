# apps/catalog/models/product_variant.py
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations

from django.db import models
from django.db.models import CheckConstraint, Q
from django.db.models.functions import Now


class ProductVariant(models.Model):
    """
    Sellable unit (SKU). Holds SKU/EAN, packaging, logistics data,
    order constraints, and optional list price (UVP/MSRP).
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
