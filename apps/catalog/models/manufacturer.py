#!/usr/bin/env python3

# apps/catalog/models/manufacturer.py
"""
Purpose:
    Represent manufacturer (brand or vendor) master data used in the catalog.
    Provides a stable numeric code and optional description for consistent
    brand identification across products and variants.

Context:
    Part of the `catalog` app. Serves as a reference table to associate
    products and variants with their brand/vendor for classification,
    reporting, and external integrations.

Fields:
    - manufacturer_code (SmallIntegerField, PK): Stable business code
      uniquely identifying the manufacturer.
    - manufacturer_description (CharField, max 200): Optional descriptive
      name or label for the manufacturer.

Relations:
    - Referenced by Product and ProductVariant models to indicate brand/vendor.

Used by:
    - Catalog (Product, ProductVariant)
    - Procurement and reporting modules requiring brand information

Depends on:
    - Django ORM

Example:
    >>> from apps.catalog.models import Manufacturer
    >>> Manufacturer.objects.create(manufacturer_code=101, manufacturer_description="ACME Tools")
    <Manufacturer: 101 — ACME Tools>
"""


from __future__ import annotations
from django.db import models


class Manufacturer(models.Model):
    """Manufacturer master data (brand/vendor entity for catalog)."""

    manufacturer_code = models.SmallIntegerField(
        primary_key=True,
        help_text="Business code for the manufacturer (small integer).",
    )
    manufacturer_description = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional description/name of the manufacturer.",
    )

    class Meta:
        #db_table = "manufacturer"
        verbose_name = "Manufacturer"
        verbose_name_plural = "Manufacturers"

    def __str__(self) -> str:
        return (
            f"{self.manufacturer_code} — "
            f"{self.manufacturer_description or 'Manufacturer'}"
        )
