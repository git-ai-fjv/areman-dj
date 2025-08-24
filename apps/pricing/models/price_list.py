# Created according to the user's Copilot Base Instructions.

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
