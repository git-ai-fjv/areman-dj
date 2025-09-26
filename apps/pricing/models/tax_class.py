# apps/pricing/models/tax_class.py
"""
Purpose:
    Defines tax classes for products and services, including name and rate.
    Used to determine applicable tax percentages (e.g., 19% VAT).

Context:
    Part of the pricing domain. Each TaxClass represents a distinct taxation
    rule that can be applied to price calculations in ERP and shop systems.

Fields:
    - name (CharField, unique): Human-readable name for the tax class (e.g., "Standard VAT").
    - rate (DecimalField, 5,4): Tax rate as a decimal fraction (0–1, e.g., 0.1900 = 19%).
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - May be referenced by products, price rules, or invoice logic in other models.

Used by:
    - Pricing and billing systems to apply the correct tax rate
    - ERP processes for compliance and reporting
    - Import and catalog services for mapping external tax definitions

Depends on:
    - Django ORM (validation and constraints)

Example:
    >>> from apps.pricing.models import TaxClass
    >>> vat = TaxClass.objects.create(name="Standard VAT", rate="0.1900")
    >>> print(vat)
    Standard VAT (0.1900)
"""


from __future__ import annotations

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.functions import Now
from django.db.models import Q


class TaxClass(models.Model):
    #id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    rate = models.DecimalField(
        max_digits=5, decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )

    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"{self.name} ({self.rate})"

    class Meta:
        db_table = "tax_class"
        indexes = [
            models.Index(fields=("rate",), name="idx_tax_class_rate"),
        ]
        constraints = [
            models.CheckConstraint(
                name="ck_tax_class_rate",
                check=Q(rate__gte=0) & Q(rate__lte=1),
            ),
        ]


