
# apps/catalog/models/product_media.py
"""
Purpose:
    Stores media assets (images, videos, documents) for products and variants.
    Each entry represents one media file with metadata, linked either to a
    Product or to a specific ProductVariant.

Context:
    Part of the `catalog` app. Used to manage product images, thumbnails,
    and other media for display in shop systems and marketplaces.

Fields:
    - id (BigAutoField): Primary key.
    - organization (FK → core.Organization): Owner of the media record.
    - product (FK → catalog.Product): Product to which this media belongs.
    - variant (FK → catalog.ProductVariant, optional): Specific variant if media
      is variant-specific; otherwise null.
    - role (CharField, 20): Media role (e.g., "gallery", "thumbnail").
    - sort_order (SmallIntegerField): Ordering within the role group.
    - alt_text (CharField, 200): Alternative text for accessibility/SEO.
    - media_url (TextField): URL to the media file (e.g., CDN link).
    - mime (CharField, 100): MIME type if available (e.g., image/jpeg).
    - width_px / height_px (IntegerField): Dimensions of the media (optional).
    - file_size (IntegerField): File size in bytes (optional).
    - is_active (BooleanField): Active flag for filtering.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Organization → multiple ProductMedia
    - Product → multiple ProductMedia
    - ProductVariant → multiple ProductMedia (optional)

Used by:
    - apps.catalog.models.Product (reverse FK)
    - apps.catalog.models.ProductVariant (reverse FK)
    - API / frontend layers for rendering product galleries

Depends on:
    - core.Organization
    - catalog.Product
    - catalog.ProductVariant

Example:
    >>> from apps.catalog.models import ProductMedia
    >>> pm = ProductMedia.objects.create(
    ...     organization=org,
    ...     product=prod,
    ...     role="gallery",
    ...     media_url="https://cdn.example.com/img123.jpg",
    ...     alt_text="Front view of the product"
    ... )
    >>> print(pm)
    [org=1] product=123 gallery #1
"""


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

