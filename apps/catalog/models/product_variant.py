#!/usr/bin/env python3
# Created according to the user's Copilot Base Instructions.
from __future__ import annotations

from django.db import models
from django.db.models import CheckConstraint, Q
from django.db.models.functions import Now


class ProductVariant(models.Model):
    """Sellable unit (SKU) with org guard and business key on (packing, origin, state)."""

    # PK (BIGSERIAL)
    #id = models.BigAutoField(primary_key=True)

    # org_code SMALLINT → FK to core.Organization(org_code)
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
        related_name="product_variants",
    )

    # product_id BIGINT → FK to catalog.Product(id)
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
    barcode = models.CharField(max_length=64, blank=True, null=True)

    # Extended attributes (from legacy `items`)
    #packing_code = models.SmallIntegerField(default=2)      # composite FK to packing in SQL migration
    #origin_code = models.CharField(max_length=1)
    #state_code = models.CharField(max_length=1)
    customs_code = models.IntegerField(default=0)
    weight = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    is_active = models.BooleanField(default=True)

    # DB fills timestamps via DEFAULT NOW()
    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"[org={self.organization}] SKU={self.sku} (product_id={self.product_id})"

    class Meta:
        #db_table = "product_variant"
        # indexes = [
        #     models.Index(fields=("organization",), name="idx_variant_org"),
        #     models.Index(fields=("product",), name="idx_variant_product"),
        #     models.Index(fields=("is_active",), name="idx_variant_active"),
        # ]
        constraints = [
            # CHECKs
            #CheckConstraint(check=Q(customs_code__gte=0), name="ck_variant_customs_nonneg"),
            CheckConstraint(check=Q(weight__gte=0), name="ck_variant_weight_nonneg"),

            # (org_code, sku) unique
            models.UniqueConstraint(fields=("organization", "sku"), name="uniq_variant_org_sku"),

            # Guard pattern
            models.UniqueConstraint(fields=("organization", "id"), name="uniq_variant_org_id"),

            # Business key: one (packing, origin, state) per product+org
            models.UniqueConstraint(
                fields=("organization", "product", "packing", "origin", "state"),
                name="uniq_variant_org_product_pack_origin_state",
            ),
        ]
