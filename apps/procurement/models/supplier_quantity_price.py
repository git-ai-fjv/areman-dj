# apps/procurement/models/supplier_quantity_price.py
# Created according to the user's permanent Copilot Base Instructions.
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

