# Created according to the user's permanent Copilot Base Instructions.
# apps/procurement/models/supplier_product.py

from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.db.models.functions import Now
from django.core.validators import MinValueValidator


class SupplierProduct(models.Model):
    #id = models.BigAutoField(primary_key=True)

    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
        related_name="supplier_products",
    )

    supplier = models.ForeignKey(
        "partners.Supplier",
        on_delete=models.PROTECT,
        related_name="supplier_products",
    )

    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.PROTECT,
        related_name="supplier_products",
    )

    supplier_sku = models.CharField(max_length=100)
    pack_size = models.DecimalField(
        max_digits=10, decimal_places=3, default=1,
        validators=[MinValueValidator(0.001)]
    )
    min_order_qty = models.DecimalField(
        max_digits=10, decimal_places=3, default=0,
        validators=[MinValueValidator(0)]
    )
    lead_time_days = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    is_active = models.BooleanField(default=True)
    notes = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"[org={self.organization}] supp={self.supplier} sku={self.supplier_sku} -> variant={self.variant}"

    class Meta:
        # db_table = "supplier_product"
        # indexes = [
        #     models.Index(fields=("organization",), name="idx_spp_org"),
        #     models.Index(fields=("supplier",),    name="idx_spp_supplier"),
        #     models.Index(fields=("variant",),     name="idx_spp_variant"),
        #     models.Index(fields=("is_active",),   name="idx_spp_active"),
        #     models.Index(fields=("supplier_sku",),name="idx_spp_sku"),
        # ]
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "variant", "supplier"),
                name="uniq_spp_supplier_sku",
            ),
            models.CheckConstraint(name="ck_spp_pack_pos",   check=Q(pack_size__gt=0)),
            models.CheckConstraint(name="ck_spp_moq_nonneg", check=Q(min_order_qty__gte=0)),
            models.CheckConstraint(name="ck_spp_lead_nonneg",check=Q(lead_time_days__gte=0)),
        ]


