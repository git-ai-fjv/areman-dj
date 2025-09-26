# apps/core/models/currency.py
"""
Purpose:
    Reference table for ISO-4217 currencies.
    Stores currency code, name, symbol, decimal precision, and active status.

Context:
    Used throughout the system to enforce consistent currency handling
    (pricing, procurement, sales, finance).

Fields:
    - code (CharField, PK): ISO 4217 currency code (e.g., "USD", "EUR").
    - name (CharField): Full currency name (e.g., "US Dollar").
    - symbol (CharField): Display symbol (e.g., "$", "€").
    - decimal_places (SmallInteger): Allowed decimals (0–6; EUR=2).
    - is_active (Bool): Whether this currency is active.
    - created_at / updated_at: System timestamps, DB-managed.

Constraints:
    - decimal_places must be between 0 and 6.

Example:
    >>> from apps.core.models import Currency
    >>> eur = Currency.objects.create(code="EUR", name="Euro", symbol="€", decimal_places=2)
    >>> str(eur)
    'EUR — Euro'
"""





from __future__ import annotations

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.functions import Now


class Currency(models.Model):
    """ISO-4217 Währungen mit Anzeige-Infos und Aktiv-Flag."""

    # code CHAR(3) PRIMARY KEY
    code = models.CharField(primary_key=True, max_length=3)

    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=8, null=True, blank=True)

    # 0..6 (EUR=2) – validieren in App + DB
    decimal_places = models.SmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(6)]
    )

    is_active = models.BooleanField(default=True)

    # DB setzt Timestamps (keine auto_now*; wir spiegeln nur die Spalten)
    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


