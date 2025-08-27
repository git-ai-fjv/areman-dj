# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations

from django.db import models
from django.db.models.functions import Now


class SupplierPrice(models.Model):
    """
    Supplier-specific purchasing price header.
    Holds currency, validity, and flags.
    Concrete price tiers are stored in SupplierQuantityPrice.
    """

    supplier_product = models.ForeignKey(
        "procurement.SupplierProduct",
        on_delete=models.CASCADE,
        related_name="prices",
    )

    currency = models.ForeignKey(
        "core.Currency",
        on_delete=models.PROTECT,
        related_name="supplier_prices",
        help_text="Currency of this price list (ISO 4217).",
    )

    # Optional: in some APIs there is a flat price without tiers
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Fallback flat unit price (without VAT). May be omitted if quantity prices exist.",
    )
    min_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Fallback minimum quantity for the flat price. Null if only tiers exist.",
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
                fields=("supplier_product", "currency", "valid_from"),
                name="uniq_supplier_price_header",
            ),
        ]

    def __str__(self) -> str:
        if self.unit_price is not None:
            return f"{self.supplier_product} {self.unit_price} {self.currency.code}"
        return f"{self.supplier_product} {self.currency.code} (tiered)"
