# apps/catalog/models/channel.py
# Created according to the user's Copilot Base Instructions.



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
