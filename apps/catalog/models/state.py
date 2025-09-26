#!/usr/bin/env python3
# apps/catalog/models/state.py
"""
Purpose:
    Defines the State master data entity, represented by a single-letter code.
    Used to classify product variants by condition/state within the catalog.

Context:
    Part of the `catalog` app. Each ProductVariant references a State to
    indicate its condition (e.g., new, refurbished, used).

Fields:
    - state_code (CharField, 1, PK): Single-letter identifier of the state.
    - state_description (CharField, 100): Optional descriptive label.

Relations:
    - ProductVariant → references State via FK.

Used by:
    - apps.catalog.models.ProductVariant (FK relation via state)

Depends on:
    - Django ORM
    - core.Organization (indirectly via ProductVariant usage)

Example:
    >>> from apps.catalog.models import State
    >>> s = State.objects.create(state_code="N", state_description="New")
    >>> print(s)
    N — New
"""

from __future__ import annotations
from django.db import models


class State(models.Model):
    """State master data (single-letter code)."""

    state_code = models.CharField(
        max_length=1,
        primary_key=True,
        help_text="Single-letter state code.",
    )
    state_description = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional description/name of the state.",
    )

    class Meta:
        #db_table = "state"
        verbose_name = "State"
        verbose_name = "State"
        verbose_name_plural = "States"

    def __str__(self) -> str:
        return f"{self.state_code} — {self.state_description or 'State'}"

