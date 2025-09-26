#!/usr/bin/env python3

# apps/catalog/models/packing.py
"""
Purpose:
    Define packaging unit master data within an organization.
    Each record specifies how items are packed (e.g., single piece,
    box of 10, pallet), including codes, multipliers, and descriptions.

Context:
    Part of the `catalog` app. Used in product and procurement workflows
    to enforce packaging rules for ordering, stock management, and logistics.

Fields:
    - id (AutoField): Surrogate primary key (SERIAL in SQL).
    - organization (FK → core.Organization): Owning organization,
      ensures tenant isolation.
    - packing_code (SmallIntegerField): Business code identifying
      the packing unit within an organization.
    - amount (DecimalField, NUMERIC(10,3)): Multiplier for this unit
      (default 1.000, e.g. "box of 10").
    - packing_short_description (CharField, max 20): Short label for display.
    - packing_description (CharField, max 200): Longer optional description.

Relations:
    - Organization → multiple Packing definitions.
    - Referenced by ProductVariant or Procurement models for correct packaging
      and order handling.

Used by:
    - Catalog (ProductVariant definition)
    - Procurement (ordering logic, minimum order units)

Depends on:
    - Django ORM
    - core.Organization

Example:
    >>> from apps.catalog.models import Packing
    >>> Packing.objects.create(
    ...     organization=org,
    ...     packing_code=10,
    ...     amount=Decimal("10.000"),
    ...     packing_short_description="Box of 10",
    ... )
    <Packing: 10 — Box of 10>
"""


from __future__ import annotations

from decimal import Decimal

from django.db import models


class Packing(models.Model):
    """Represents a packaging unit definition within an organization.

    Mirrors the given SQL schema:
      CREATE TABLE packing (
          id SERIAL PRIMARY KEY,
          org_code SMALLINT NOT NULL,
          packing_code SMALLINT NOT NULL,
          amount NUMERIC(10, 3) DEFAULT 1.0,
          packing_short_description VARCHAR(20) NOT NULL,
          packing_description VARCHAR(200)
      );
      ALTER TABLE packing
        ADD CONSTRAINT fk_packing_org
          FOREIGN KEY (org_code) REFERENCES org(org_code) ON DELETE RESTRICT;
      ALTER TABLE packing
        ADD CONSTRAINT uniq_packing_packing_code_org_code
          UNIQUE (org_code, packing_code);
    """

    # Match SERIAL (int4). If the project default is BigAutoField, keep this explicit AutoField.
    #id = models.AutoField(primary_key=True)

    # FK to Organization by its code field, stored in column "org_code".
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,  # ON DELETE RESTRICT
        related_name="packings",
    )

    packing_code = models.SmallIntegerField()
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal("1.000"),
        null=True,  # nullable in SQL; default still applies when not provided
        help_text="Multiplier amount for this packing unit.",
    )
    packing_short_description = models.CharField(max_length=20)
    packing_description = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "packing_code"],
                name="uniq_packing_packing_code_org_code",
            ),
        ]
        # indexes = [
        #     models.Index(fields=["organization"], name="idx_packing_org"),
        # ]

    def __str__(self) -> str:
        """Human-readable representation used in admin and logs."""
        return f"{self.packing_code} — {self.packing_short_description}"
