# apps/catalog/models/product.py

# apps/catalog/models/product.py
"""
Purpose:
    Define master product data shared across all variants.
    Stores catalog-wide attributes such as name, manufacturer,
    part number, SEO metadata, and marketing flags.

Context:
    Part of the `catalog` app. Products serve as the base entity for
    all sellable variants (ProductVariant) and are referenced by
    channel-specific models. Provides a stable anchor for procurement,
    pricing, and shop integration.

Fields:
    - id (AutoField): Primary key.
    - organization (FK → core.Organization): Owning organization.
    - name (CharField, 200): Human-readable product name.
    - slug (CharField, 200): Unique slug within an organization.
    - manufacturer (FK → catalog.Manufacturer): Brand or vendor.
    - manufacturer_part_number (CharField, 100): Raw part number.
    - manufacturer_part_number_norm (GeneratedField, 100): Normalized part
      number, computed via PostgreSQL `REGEXP_REPLACE`.
    - product_group (FK → catalog.ProductGroup): Classification/group.
    - description (TextField): Long product description, optional.
    - meta_title / meta_description / keywords: SEO fields.
    - is_new (Boolean): Marketing flag (new release).
    - is_closeout (Boolean): Marketing flag (discontinued).
    - release_date (DateField): Release information.
    - is_active (Boolean): Availability flag.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Organization → multiple Products.
    - Manufacturer → multiple Products.
    - ProductGroup → multiple Products.
    - Referenced by ProductVariant and ChannelVariant.

Used by:
    - Catalog (ProductVariant definitions).
    - Pricing and Procurement modules.
    - External integrations (shop systems, supplier APIs).

Depends on:
    - Django ORM
    - core.Organization
    - catalog.Manufacturer
    - catalog.ProductGroup

Example:
    >>> from apps.catalog.models import Product
    >>> Product.objects.filter(
    ...     organization__org_code=1,
    ...     is_active=True,
    ...     is_closeout=False,
    ... )
"""


from __future__ import annotations

from django.db import models
from django.db.models import F, Value, Func
from django.db.models.functions import Lower, Now


class RegexpReplace(Func):
    """PostgreSQL REGEXP_REPLACE(source, pattern, replacement [, flags])."""
    function = "REGEXP_REPLACE"
    template = "%(function)s(%(expressions)s)"


class Product(models.Model):
    """
    Product master data (shared across variants).
    Mirrors supplier API fields plus ERP/Shop attributes.
    """

    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
        related_name="products",
    )

    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=200)

    manufacturer = models.ForeignKey(
        "catalog.Manufacturer",
        on_delete=models.PROTECT,
        related_name="products",
    )

    manufacturer_part_number = models.CharField(max_length=100)

    manufacturer_part_number_norm = models.GeneratedField(
        expression=RegexpReplace(
            RegexpReplace(
                RegexpReplace(
                    RegexpReplace(
                        RegexpReplace(
                            Lower(F("manufacturer_part_number")),
                            Value("[ßẞ]"), Value("ss"), Value("g")
                        ),
                        Value("ä"), Value("ae"), Value("g")
                    ),
                    Value("ö"), Value("oe"), Value("g")
                ),
                Value("ü"), Value("ue"), Value("g")
            ),
            Value("[^0-9a-z]+"),
            Value(""),
            Value("g"),
        ),
        output_field=models.CharField(max_length=100),
        db_persist=True,
        editable=False,
    )

    product_group = models.ForeignKey(
        "catalog.ProductGroup",
        on_delete=models.PROTECT,
    )

    description = models.TextField(
        null=True,
        blank=True,
        help_text="Full product description (rich text / HTML).",
    )

    # SEO / Marketing
    meta_title = models.CharField(max_length=255, null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    keywords = models.CharField(max_length=500, null=True, blank=True)

    # Shop flags
    is_new = models.BooleanField(default=False)
    is_closeout = models.BooleanField(default=False)
    release_date = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"[{self.organization}] {self.name} ({self.slug})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "slug"),
                name="uniq_product_org_slug",
            ),
            models.UniqueConstraint(
                fields=("organization", "manufacturer", "manufacturer_part_number_norm"),
                name="uniq_product_org_manu_mpn_norm",
            ),
            models.UniqueConstraint(
                fields=("organization", "id"),
                name="uniq_product_org_id",
            ),
        ]


