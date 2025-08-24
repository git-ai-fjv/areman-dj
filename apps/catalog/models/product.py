# Created according to the user's Copilot Base Instructions.
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
    Mirrors the SQL table `product` (BIGINT id, MPN normalization, item group).
    """

    #id = models.BigAutoField(primary_key=True)

    # org_code SMALLINT → FK to core.Organization(org_code)
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
    )

    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=200)

    # manufacturer_code SMALLINT → FK to catalog.Manufacturer(manufacturer_code)
    manufacturer = models.ForeignKey(
        "catalog.Manufacturer",
        on_delete=models.PROTECT,
    )

    manufacturer_part_number = models.CharField(max_length=100)

    # Normalized MPN: lower + de-umlauts + strip non [0-9a-z]
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
        output_field=models.CharField(max_length=200),
        db_persist=True,
        editable=False,
    )

    # ✅ Echte ORM-Referenz auf Artikelgruppe
    product_group = models.ForeignKey(
        "catalog.ProductGroup",
        on_delete=models.PROTECT,
    )

    is_active = models.BooleanField(default=True)

    # DB-defaults: Postgres setzt NOW(); Django lässt Spalten leer beim INSERT
    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"[{self.organization} {self.name} ({self.slug})"

    class Meta:
#        db_table = "product"
#         indexes = [
#             models.Index(fields=("organization",), name="idx_product_org"),
#             models.Index(fields=("is_active",), name="idx_product_active"),
#             models.Index(fields=("manufacturer",), name="idx_product_manufacturer"),
#         ]
         constraints = [
            # (org_code, slug) unique
            models.UniqueConstraint(
                fields=("organization", "slug"),
                name="uniq_product_org_slug",
            ),
            # (org_code, manufacturer_code, manufacturer_part_number_norm) unique
            models.UniqueConstraint(
                fields=("organization", "manufacturer", "manufacturer_part_number_norm"),
                name="uniq_product_org_manu_mpn_norm",
            ),
            # Guard für Varianten: (org_code, id)
            models.UniqueConstraint(
                fields=("organization", "id"),
                name="uniq_product_org_id",
            ),
        ]
