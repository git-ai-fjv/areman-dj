# apps/catalog/models/product.py
# Created according to the user's permanent Copilot Base Instructions.
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


