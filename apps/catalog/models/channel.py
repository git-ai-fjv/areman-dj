# apps/catalog/models/channel.py
"""
Purpose:
    Define the Channel model representing a sales or distribution channel
    (e.g., webshop, marketplace) within an organization. Captures its code,
    name, kind, and base currency.

Context:
    Part of the `catalog` app. Channels represent the entry points through which
    products and prices are published. They are used in pricing, procurement,
    and integration with external systems (e.g., shops, marketplaces).

Fields:
    - id (AutoField): Primary key for the channel.
    - organization (FK → core.Organization): The owning organization.
    - channel_code (CharField, max 20): Short code identifying the channel
      within an organization (unique per organization).
    - channel_name (CharField, max 200): Human-readable channel name.
    - kind (CharField, max 50): Type of channel ("shop" or "marketplace").
    - base_currency (FK → core.Currency): Currency in which prices are defined.
    - is_active (BooleanField): Whether this channel is active.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Organization → multiple Channels
    - Currency → multiple Channels
    - Channel ↔ Product/Variant pricing via related models (e.g. ChannelVariant)

Used by:
    - Pricing (PriceGroup, PriceList, SalesChannelVariantPrice)
    - Procurement (for supplier channel relations, if applicable)
    - Services for integration with external systems

Depends on:
    - Django ORM
    - core.Organization
    - core.Currency

Example:
    # Get all active marketplace channels for org 1
    Channel.objects.filter(organization__org_code=1, kind="marketplace", is_active=True)
"""




from __future__ import annotations

from django.db import models
from django.db.models.functions import Now


class Channel(models.Model):
    id = models.AutoField(primary_key=True)

    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
        related_name="channels",
    )

    channel_code = models.CharField(max_length=20)
    channel_name = models.CharField(max_length=200)

    kind = models.CharField(max_length=50, default="shop")  # 'shop' | 'marketplace'

    base_currency = models.ForeignKey(
        "core.Currency",
        on_delete=models.PROTECT,
        related_name="channels",

    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"[{self.organization}] {self.channel_code} — {self.channel_name}"

    class Meta:
        #db_table = "channel"
        # indexes = [
        #     models.Index(fields=("organization",), name="idx_channel_org"),
        #     models.Index(fields=("is_active",), name="idx_channel_active"),
        #     models.Index(fields=("kind",), name="idx_channel_kind"),
        # ]
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "channel_code"),
                name="uniq_channel_org_code",
            ),
            models.UniqueConstraint(
                fields=("organization", "id"),
                name="uniq_channel_org_id",
            ),
            # Falls du den enum-artigen Check möchtest, aktivieren:
            # models.CheckConstraint(
            #     name="ck_channel_kind",
            #     check=models.Q(kind__in=["shop", "marketplace"]),
            # ),
        ]
