# apps/pricing/models/price_group.py
"""
Purpose:
    Represents a logical grouping of prices within an organization.
    Allows categorization of product or customer prices into groups
    such as retail, wholesale, or special contract pricing.

Context:
    Belongs to the pricing domain. PriceGroups are used to define
    customer-specific or organization-specific pricing structures.

Fields:
    - organization (FK → core.Organization): The owning organization.
    - price_group_code (CharField, max 20): Unique code per organization.
    - price_group_description (CharField, max 200): Optional descriptive name.

Relations:
    - Organization → multiple PriceGroups
    - Referenced by PriceList or SalesChannelVariantPrice
      to determine applicable prices.

Used by:
    - Pricing logic for ERP/shops
    - Import routines that map supplier/customer pricing
    - Reporting modules for analyzing price segmentation

Depends on:
    - apps.core.models.Organization

Example:
    >>> from apps.pricing.models import PriceGroup
    >>> pg = PriceGroup.objects.create(
    ...     organization=org,
    ...     price_group_code="WHOLESALE",
    ...     price_group_description="Wholesale customer pricing"
    ... )
    >>> print(pg)
    WHOLESALE — Wholesale customer pricing
"""


from __future__ import annotations
from django.db import models


class PriceGroup(models.Model):
    """Price group master data, scoped by organization."""

    # Force 32-bit PK (SERIAL-like). Remove to use project default (BigAutoField).
   # id = models.AutoField(primary_key=True)

    # FK to core.Organization(org_code); DB column stays 'org_code'
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,  # ON DELETE RESTRICT equivalent
        related_name="price_groups",
    )

    price_group_code = models.CharField(
        max_length=20,
        help_text="Price group code (unique within organization).",
    )
    price_group_description = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional description/name of the price group.",
    )

    class Meta:
        #db_table = "price_group"
        verbose_name = "Price Group"
        verbose_name_plural = "Price Groups"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "price_group_code"],
                name="uniq_price_group_org_code",
            )
        ]
        # indexes = [
        #     models.Index(fields=["organization"], name="idx_price_group_org"),
        # ]

    def __str__(self) -> str:
        return f"{self.price_group_code} — {self.price_group_description or 'Price Group'}"
