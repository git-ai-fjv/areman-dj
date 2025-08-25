# apps/catalog/models/channel_variant.py
# Created according to the user's Copilot Base Instructions.
# the

from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.db.models.functions import Now


class ChannelVariant(models.Model):
    """
    A product variant in a sales channel (e.g. a webshop).
    Links a ProductVariant to a Channel, with additional fields for
    publication status, external IDs, and metadata.
    Represents the availability and configuration of a specific product variant
    within a specific sales channel.
    Each ChannelVariant is unique per (organization, channel, variant).
    1:n relation: A ProductVariant can be linked to multiple Channels via ChannelVariant.
    1:n relation: A Channel can have multiple ProductVariants via ChannelVariant.
    1:1 relation: A ChannelVariant links exactly one ProductVariant to one Channel.
    1:1 relation: A ChannelVariant belongs to exactly one Organization.
    """
    #id = models.BigAutoField(primary_key=True)

    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
        related_name="channel_variants",
    )

    channel = models.ForeignKey(
        "catalog.Channel",
        on_delete=models.PROTECT,
        related_name="channel_variants",
    )

    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.PROTECT,
        related_name="channel_variants",
    )

    publish = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    need_shop_update = models.BooleanField(default=False)

    shop_product_id = models.CharField(max_length=100, null=True, blank=True)
    shop_variant_id = models.CharField(max_length=100, null=True, blank=True)

    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(null=True, blank=True)

    # Postgres JSONB (Django -> JSONField)
    meta_json = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"[org={self.organization}] ch={self.channel} v={self.variant} (pub={self.publish})"

    class Meta:
        # db_table = "channel_variant"
        # indexes = [
        #     models.Index(fields=("organization",), name="idx_channel_variant_org"),
        #     models.Index(fields=("channel",), name="idx_channel_variant_channel"),
        #     models.Index(fields=("variant",), name="idx_channel_variant_variant"),
        #     models.Index(fields=("publish",), name="idx_channel_variant_publish"),
        #     models.Index(fields=("is_active",), name="idx_channel_variant_active"),
        #     models.Index(fields=("need_shop_update",), name="ix_chvar_needupd"),
        #     models.Index(fields=("last_synced_at",), name="ix_chvar_lastsync"),
        # ]
        constraints = [
            # Eindeutig pro (Org, Channel, Variante)
            models.UniqueConstraint(
                fields=("organization", "channel", "variant"),
                name="uniq_channel_variant",
            ),
            # Partial-unique auf externe IDs je Channel (nur wenn gesetzt)
            # models.UniqueConstraint(
            #     fields=("channel", "shop_item_id"),
            #     name="uniq_channel_item_ext",
            #     condition=Q(shop_item_id__isnull=False) & ~Q(shop_item_id=""),
            # ),
            # models.UniqueConstraint(
            #     fields=("channel", "shop_variant_id"),
            #     name="uniq_channel_variant_ext",
            #     condition=Q(shop_variant_id__isnull=False) & ~Q(shop_variant_id=""),
            # ),
        ]

