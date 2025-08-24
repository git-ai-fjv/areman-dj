# apps/pricing/models/channel_price_list.py
# Created according to the user's Copilot Base Instructions.

from __future__ import annotations

from django.db import models
from django.db.models.functions import Now


class ChannelPriceList(models.Model):
    id = models.BigAutoField(primary_key=True)

    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
        related_name="channel_price_lists",
    )

    channel = models.ForeignKey(
        "catalog.Channel",
        on_delete=models.PROTECT,
        related_name="channel_price_lists",
    )

    price_list = models.ForeignKey(
        "pricing.PriceList",
        on_delete=models.PROTECT,
        related_name="channel_price_lists",
    )

    role = models.CharField(max_length=20, default="sale")   # 'sale', 'compare', ...
    priority = models.SmallIntegerField(default=1)           # 1 = primär, >1 Fallback
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"[org={self.organization_id}] ch={self.channel_id} role={self.role} prio={self.priority} -> pl={self.price_list_id}"

    class Meta:
        # db_table = "channel_price_list"
        # indexes = [
        #     models.Index(fields=("organization",), name="idx_chpl_org"),
        #     models.Index(fields=("channel",), name="idx_chpl_chan"),
        #     models.Index(fields=("role",), name="idx_chpl_role"),
        #     models.Index(fields=("is_active",), name="idx_chpl_active"),
        # ]
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "channel", "price_list"),
                name="uniq_chpl_org_chan_pl",
            ),
            models.UniqueConstraint(
                fields=("organization", "channel", "role", "priority"),
                name="uniq_chpl_org_chan_role_pri",
            ),
        ]

