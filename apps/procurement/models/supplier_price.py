# apps/procurement/models/supplier_price.py
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations

from django.db import models
from django.db.models.functions import Now
from django.core.validators import MinValueValidator


class SupplierPrice(models.Model):
    """
    Supplier-specific purchasing price information.
    Supports multiple price tiers, currencies and validity periods.
    """

    supplier_product = models.ForeignKey(
        "procurement.SupplierProduct",
        on_delete=models.CASCADE,
        related_name="prices",
    )

    # Price attributes
    currency = models.CharField(
        max_length=3,
        default="EUR",
        help_text="ISO 4217 currency code (e.g. EUR, USD).",
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)],
        help_text="Net purchase price per unit (without VAT).",
    )
    min_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=1,
        validators=[MinValueValidator(0.001)],
        help_text="Minimum quantity for this price tier.",
    )

    # Validity
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)

    # Meta
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    class Meta:
        verbose_name = "Supplier Price"
        verbose_name_plural = "Supplier Prices"
        constraints = [
            models.UniqueConstraint(
                fields=("supplier_product", "currency", "min_quantity", "valid_from"),
                name="uniq_supplier_price_tier",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.supplier_product.supplier} {self.unit_price} {self.currency} "
            f"(min {self.min_quantity})"
        )
