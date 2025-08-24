#!/usr/bin/env python3
# Created according to the user's permanent Copilot Base Instructions.
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
