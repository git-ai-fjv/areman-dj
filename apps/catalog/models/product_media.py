# apps/catalog/models/product_media.py
# Created according to the user's Copilot Base Instructions.



from __future__ import annotations

from django.db import models
from django.db.models.functions import Now


class ProductMedia(models.Model):
    id = models.BigAutoField(primary_key=True)

    # org_code SMALLINT → FK core.Organization(org_code)
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
        related_name="products_media",

    )

    # product / variant Bezug
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="products_media",

    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="products_media",
    )

    # Medien-Metadaten
    role = models.CharField(max_length=20, default="gallery")
    sort_order = models.SmallIntegerField(default=0)
    alt_text = models.CharField(max_length=200, default="", blank=True)

    media_url = models.TextField()
    mime = models.CharField(max_length=100, null=True, blank=True)
    width_px = models.IntegerField(null=True, blank=True)
    height_px = models.IntegerField(null=True, blank=True)
    file_size = models.IntegerField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        scope = f"variant={self.variant}" if self.variant else f"product={self.product}"
        return f"[org={self.organization}] {scope} {self.role} #{self.id}"

    class Meta:
        #db_table = "product_media"
        indexes = [
            models.Index(fields=("organization",), name="idx_product_media_org"),
            models.Index(fields=("product",), name="idx_product_media_product"),
            models.Index(fields=("variant",), name="idx_product_media_variant"),
            models.Index(fields=("role", "sort_order"), name="idx_product_media_role_order"),
            models.Index(fields=("is_active",), name="idx_product_media_active"),
        ]

