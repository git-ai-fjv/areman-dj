# apps/pricing/models/price_list.py
"""
Purpose:
    Represents a price list definition within an organization.
    Each price list groups together prices in a given currency and
    can be used for either sales or procurement contexts.

Context:
    Belongs to the pricing domain. PriceLists are the containers for
    product/variant pricing records and are associated with a single currency.

Fields:
    - organization (FK → core.Organization): The owning organization.
    - price_list_code (CharField, max 20): Unique code per organization.
    - price_list_description (CharField, max 200): Human-readable description.
    - kind (CharField, max 1): Type of list, 'S' (sales) or 'P' (procurement).
    - currency (FK → core.Currency): Currency of all prices in this list.
    - is_active (BooleanField): Whether the price list is active.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Organization → multiple PriceLists
    - Currency → multiple PriceLists
    - PriceList → referenced by price detail tables (e.g., variant prices)

Used by:
    - Sales processes to fetch customer price lists
    - Procurement processes to manage supplier price lists
    - Pricing services and ERP import routines

Depends on:
    - apps.core.models.Organization
    - apps.core.models.Currency

Example:
    >>> from apps.pricing.models import PriceList
    >>> pl = PriceList.objects.create(
    ...     organization=org,
    ...     price_list_code="RETAIL-2025",
    ...     price_list_description="Retail price list for 2025",
    ...     kind="S",
    ...     currency=eur
    ... )
    >>> print(pl)
    [Org1] RETAIL-2025 (S)
"""


from __future__ import annotations

from django.db import models
from django.db.models.functions import Now


class PriceList(models.Model):
    #id = models.AutoField(primary_key=True)

    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
        related_name="price_lists",
    )

    price_list_code = models.CharField(max_length=20)
    price_list_description = models.CharField(max_length=200)
    kind = models.CharField(max_length=1)  # 'S' or 'P'

    currency = models.ForeignKey(
        "core.Currency",
        on_delete=models.PROTECT,
        related_name="price_lists",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"[{self.organization}] {self.price_list_code} ({self.kind})"

    class Meta:
        # db_table = "price_list"
        # indexes = [
        #     models.Index(fields=("organization",), name="idx_price_list_org"),
        #     models.Index(fields=("is_active",), name="idx_price_list_active"),
        #     models.Index(fields=("kind",), name="idx_price_list_kind"),
        # ]
        constraints = [
            # (org_code, price_list_code) unique
            models.UniqueConstraint(
                fields=("organization", "price_list_code"),
                name="uniq_price_list_org_code",
            ),
            # Guard für Org-Konsistenz (für spätere price-Guards)
            models.UniqueConstraint(
                fields=("organization", "id"),
                name="uniq_price_list_org_id",
            ),
            models.CheckConstraint(
                name="ck_price_list_kind",
                check=models.Q(kind__in=["S", "P"]),
            ),
        ]
