# apps/procurement/models/supplier_product.py
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.db.models.functions import Now
from django.core.validators import MinValueValidator


class SupplierProduct(models.Model):
    """
    Links a ProductVariant with a specific supplier.
    Holds supplier-specific identifiers, packaging,
    ordering constraints and procurement metadata.
    """

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

    # Identification at supplier side
    supplier_sku = models.CharField(
        max_length=100,
        help_text="Article number / SKU as used by the supplier."
    )
    supplier_description = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Optional description as provided by supplier (may differ from catalog description).",
    )

    # Procurement attributes
    pack_size = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=1,
        validators=[MinValueValidator(0.001)],
        help_text="Number of base units in one pack as sold by supplier.",
    )
    min_order_qty = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Minimum order quantity (MOQ) at supplier.",
    )
    lead_time_days = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Standard lead time in days until delivery.",
    )

    # Flags
    is_active = models.BooleanField(default=True)
    is_preferred = models.BooleanField(
        default=False,
        help_text="Marks the preferred supplier for this variant."
    )

    notes = models.TextField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return (
            f"[org={self.organization}] supplier={self.supplier} "
            f"sku={self.supplier_sku} -> variant={self.variant.sku}"
        )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "variant", "supplier"),
                name="uniq_supplier_product",
            ),
            models.CheckConstraint(
                name="ck_supplier_packsize_positive", check=Q(pack_size__gt=0)
            ),
            models.CheckConstraint(
                name="ck_supplier_moq_nonneg", check=Q(min_order_qty__gte=0)
            ),
            models.CheckConstraint(
                name="ck_supplier_leadtime_nonneg", check=Q(lead_time_days__gte=0)
            ),
        ]
