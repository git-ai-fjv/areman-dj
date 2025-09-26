#!/usr/bin/env python3

# apps/catalog/models/origin.py
"""
Purpose:
    Define origin master data using a single-letter code.
    Provides a lightweight reference for categorizing products
    or variants by their origin or classification.

Context:
    Part of the `catalog` app. Serves as a reference/master table
    used in product variant definitions to tag items with an origin
    attribute for logistics, reporting, or integration purposes.

Fields:
    - origin_code (CharField, PK, length=1): Unique single-letter code
      identifying the origin.
    - origin_description (CharField, max 100): Optional descriptive
      label or name for the origin.

Relations:
    - Referenced by ProductVariant and potentially other catalog models
      to denote the origin classification of an item.

Used by:
    - Catalog (ProductVariant)
    - Any downstream reporting or integration requiring origin info

Depends on:
    - Django ORM

Example:
    >>> from apps.catalog.models import Origin
    >>> Origin.objects.create(origin_code="E", origin_description="Europe")
    <Origin: E — Europe>
"""


from __future__ import annotations
from django.db import models


class Origin(models.Model):
    """Origin master data (single-letter code)."""

    origin_code = models.CharField(
        max_length=1,
        primary_key=True,
        help_text="Single-letter origin code.",
    )
    origin_description = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional description/name of the origin.",
    )

    class Meta:
        #db_table = "origin"
        verbose_name = "Origin"
        verbose_name_plural = "Origins"

    def __str__(self) -> str:
        return f"{self.origin_code} — {self.origin_description or 'Origin'}"

