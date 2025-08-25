# apps/pricing/models/price.py
# Created according to the user's Copilot Base Instructions.



from __future__ import annotations

from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Q
from django.db.models.functions import Now


class SalesChannelVariantPrice(models.Model):
    #id = models.BigAutoField(primary_key=True)

    # Orga
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
        related_name="sales_channel_variant_prices",
    )

    # Beziehungen

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

    # Werte/Zeitfenster
    price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)],
    )

    valid_to = models.DateTimeField(null=True, blank=True)
    need_update = models.BooleanField(default=False)  # Flag to indicate if the price needs to be updated

    # DB-Defaults (Postgres setzt Timestamps)
    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"[org={self.organization}] {self.price_list}/{self.channel_variant} @ {self.amount} from {self.valid_from}"

    class Meta:
        # db_table = "price"
        # indexes = [
        #     models.Index(fields=("organization",), name="idx_price_org"),
        #     models.Index(fields=("price_list", "variant"), name="idx_price_pricelist_variant"),
        #     models.Index(fields=("variant", "price_list"), name="idx_price_variant_pricelist"),
        #     models.Index(fields=("valid_from",), name="idx_price_valid_from"),
        #     # Partial index (current price): valid_to IS NULL
        #     models.Index(
        #         fields=("price_list", "variant"),
        #         name="idx_price_current",
        #         condition=Q(valid_to__isnull=True),
        #     ),
        # ]
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "price_list", "channel_variant", "valid_from"),
                name="uniq_chanel_var_price_valid",
            ),
            models.CheckConstraint(
                check=Q(price__gte=0),
                name="ck_price_price_nonneg",
            ),
        ]

