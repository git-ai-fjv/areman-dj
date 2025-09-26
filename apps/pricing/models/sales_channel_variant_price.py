# apps/pricing/models/sales_channel_variant_price.py
"""
Purpose:
    Represents the price of a specific ChannelVariant within a PriceList.
    Each record defines the value of a variant’s price in a given sales channel
    for a specific time period.

Context:
    Belongs to the pricing domain. Used to track sales prices across
    different channels (shops, marketplaces) and supports time-based
    validity for price changes.

Fields:
    - organization (FK → core.Organization): The owning organization.
    - price_list (FK → pricing.PriceList): The price list this price belongs to.
    - channel_variant (FK → catalog.ChannelVariant): The sales channel + variant.
    - valid_from (DateTimeField): Timestamp when the price becomes effective.
    - price (DecimalField): The actual price (non-negative, up to 12,4 digits).
    - valid_to (DateTimeField): Optional end date for the price validity.
    - need_update (BooleanField): Whether the price requires a sync/update.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Organization → multiple SalesChannelVariantPrices
    - PriceList → multiple SalesChannelVariantPrices
    - ChannelVariant → multiple SalesChannelVariantPrices

Used by:
    - Pricing services to fetch current or historical prices
    - Import and sync jobs to update shop/marketplace prices
    - ERP processes for reporting and analytics

Depends on:
    - apps.core.models.Organization
    - apps.pricing.models.PriceList
    - apps.catalog.models.ChannelVariant

Example:
    >>> from apps.pricing.models import SalesChannelVariantPrice
    >>> scvp = SalesChannelVariantPrice.objects.create(
    ...     organization=org,
    ...     price_list=pl,
    ...     channel_variant=cv,
    ...     valid_from="2025-01-01T00:00:00Z",
    ...     price="99.9900"
    ... )
    >>> print(scvp)
    [org=1] RETAIL-2025/ChannelVariant(123) @ 99.9900 from 2025-01-01 00:00:00
"""


from __future__ import annotations

from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Q
from django.db.models.functions import Now


class SalesChannelVariantPrice(models.Model):
    # id = models.BigAutoField(primary_key=True)

    # Organization
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
        related_name="sales_channel_variant_prices",
    )

    # Relations
    price_list = models.ForeignKey(
        "pricing.PriceList",
        on_delete=models.PROTECT,
        related_name="sales_channel_variant_prices",
    )

    channel_variant = models.ForeignKey(
        "catalog.ChannelVariant",
        on_delete=models.PROTECT,
        related_name="sales_channel_variant_prices",
    )

    valid_from = models.DateTimeField()

    # Values / timeframe
    price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)],
    )

    valid_to = models.DateTimeField(null=True, blank=True)
    need_update = models.BooleanField(default=False)  # Flag to indicate if the price needs to be updated

    # DB defaults (Postgres sets timestamps)
    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return (
            f"[org={self.organization}] {self.price_list}/{self.channel_variant} "
            f"@ {self.price} from {self.valid_from}"
        )

    class Meta:
        # db_table = "price"
        # indexes = [
        #     models.Index(fields=("organization",), name="idx_price_org"),
        #     models.Index(fields=("price_list", "channel_variant"), name="idx_price_pricelist_variant"),
        #     models.Index(fields=("channel_variant", "price_list"), name="idx_price_variant_pricelist"),
        #     models.Index(fields=("valid_from",), name="idx_price_valid_from"),
        #     # Partial index (current price): valid_to IS NULL
        #     models.Index(
        #         fields=("price_list", "channel_variant"),
        #         name="idx_price_current",
        #         condition=Q(valid_to__isnull=True),
        #     ),
        # ]
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "price_list", "channel_variant", "valid_from"),
                name="uniq_channel_var_price_valid",
            ),
            models.CheckConstraint(
                check=Q(price__gte=0),
                name="ck_price_price_nonneg",
            ),
        ]

