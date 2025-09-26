# apps/procurement/models/supplier_quantity_price.py
"""
Purpose:
    Defines quantity-based price tiers for a supplier’s product.
    Complements SupplierPrice by enabling stepped pricing models when
    a single flat price (unit_price) is not sufficient.

Context:
    Part of the procurement domain. This model allows tiered pricing
    based on minimum order quantities. For example, buying 100 units
    may have a lower unit price than buying 10.

Fields:
    - supplier_price (FK → SupplierPrice): Links to the supplier price header.
    - min_quantity (DecimalField): Minimum quantity for this tier.
    - unit_price (DecimalField): Net purchase price per unit (excl. VAT).

Relations:
    - SupplierPrice → multiple SupplierQuantityPrice (tiers).
    - SupplierQuantityPrice belongs to exactly one SupplierPrice.

Used by:
    - Procurement calculations (choosing correct tier for an order).
    - ERP price imports from suppliers with graduated pricing.
    - PO line creation when selecting best available tier.

Depends on:
    - apps.procurement.models.SupplierPrice

Constraints:
    - Unique per (supplier_price, min_quantity).
    - Ordered by min_quantity ascending.

Example:
    >>> from apps.procurement.models import SupplierQuantityPrice
    >>> tier = SupplierQuantityPrice.objects.create(
    ...     supplier_price=sp,
    ...     min_quantity=100,
    ...     unit_price=9.99,
    ... )
    >>> print(tier)
    100+ → 9.99 (EUR)
"""

from __future__ import annotations

from django.db import models
from django.core.validators import MinValueValidator


class SupplierQuantityPrice(models.Model):
    """
    Quantity-based price tier for a supplier's product.
    Used only when SupplierPrice.unit_price is NULL.
    """

    supplier_price = models.ForeignKey(
        "procurement.SupplierPrice",
        on_delete=models.CASCADE,
        related_name="quantity_prices",
        help_text="Parent supplier price record this tier belongs to.",
    )

    min_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0.001)],
        help_text="Minimum order quantity for this tier.",
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)],
        help_text="Net purchase price per unit (without VAT).",
    )

    class Meta:
        verbose_name = "Supplier Quantity Price"
        verbose_name_plural = "Supplier Quantity Prices"
        constraints = [
            models.UniqueConstraint(
                fields=("supplier_price", "min_quantity"),
                name="uniq_supplier_quantity_price",
            )
        ]
        ordering = ["min_quantity"]

    def __str__(self) -> str:
        return f"{self.min_quantity}+ → {self.unit_price} ({self.supplier_price.currency})"

