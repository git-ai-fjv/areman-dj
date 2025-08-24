# apps/catalog/models/product_group.py
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations

from django.db import models


class ProductGroup(models.Model):
    """Product group master data, scoped by organization."""

    # Keep 32-bit PK (SERIAL-like) to match the previous model behavior.
    #id = models.AutoField(primary_key=True)

    # FK to core.Organization(org_code); DB column stays 'org_code'
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,  # maps to ON DELETE RESTRICT
        related_name="product_groups",
    )

    # ⚠ Field names remain unchanged to avoid unintended schema changes.
    item_group_code = models.CharField(
        max_length=20,
        help_text="Product group code (unique within organization).",
    )
    item_group_description = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional description/name of the product group.",
    )

    def __str__(self) -> str:
        return f"{self.item_group_code} — {self.item_group_description or 'Product Group'}"

    class Meta:
        verbose_name = "Product Group"
        verbose_name_plural = "Product Groups"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "item_group_code"],
                name="uniq_product_group_org_item_group_code",
            ),
            # NEU: für den Composite-Guard benötigt
            models.UniqueConstraint(
                fields=["organization", "id"],
                name="uniq_product_group_org_id",
            ),
        ]
        # indexes = [
        #     models.Index(fields=["organization"], name="idx_product_group_org_code"),
        # ]

