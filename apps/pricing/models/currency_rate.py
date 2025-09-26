# apps/core/models/currency_rate.py
"""
Purpose:
    Represents daily exchange rates between two currencies.
    Stores conversion factors (base → quote) with full precision
    and enforces uniqueness per date.

Context:
    Part of the core app. Used by pricing, procurement, and reporting
    to convert between currencies for transactions and analytics.

Fields:
    - base (FK → core.Currency): Base currency of the rate.
    - quote (FK → core.Currency): Quote currency of the rate.
    - rate (DecimalField, 16,8): Conversion factor (e.g., 1.12345678).
    - rate_date (DateField): Date the rate applies to.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Currency (base) → multiple CurrencyRates
    - Currency (quote) → multiple CurrencyRates

Used by:
    - Pricing and ERP calculations
    - Reports requiring currency normalization
    - Procurement processes involving multi-currency suppliers

Depends on:
    - apps.core.models.Currency
    - Django ORM (constraints, validators)

Example:
    >>> from apps.core.models import CurrencyRate, Currency
    >>> usd = Currency.objects.get(code="USD")
    >>> eur = Currency.objects.get(code="EUR")
    >>> cr = CurrencyRate.objects.create(base=usd, quote=eur, rate="0.92345678", rate_date="2025-09-26")
    >>> print(cr)
    USD/EUR @ 0.92345678 (2025-09-26)
"""

from __future__ import annotations

from django.db import models
from django.core.validators import MinValueValidator
from django.db.models.functions import Now
from django.db.models import Q


class CurrencyRate(models.Model):
    #id = models.BigAutoField(primary_key=True)

    base = models.ForeignKey(
        "core.Currency",
        on_delete=models.PROTECT,
        related_name="base_rates",
    )
    quote = models.ForeignKey(
        "core.Currency",
        on_delete=models.PROTECT,
        related_name="quote_rates",
    )

    rate = models.DecimalField(max_digits=16, decimal_places=8, validators=[MinValueValidator(0.00000001)])
    rate_date = models.DateField()

    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"{self.base_id}/{self.quote_id} @ {self.rate} ({self.rate_date})"

    class Meta:
        #db_table = "currency_rate"
        # indexes = [
        #     models.Index(fields=("rate_date",), name="idx_currency_rate_date"),
        #     models.Index(fields=("base", "quote"), name="idx_currency_rate_base_quote"),
        # ]
        constraints = [
            models.UniqueConstraint(
                fields=("base", "quote", "rate_date"),
                name="uniq_currency_rate",
            ),
            models.CheckConstraint(
                name="ck_currency_rate_positive",
                check=Q(rate__gt=0),
            ),
        ]
