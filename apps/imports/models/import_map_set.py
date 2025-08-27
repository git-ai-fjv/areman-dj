# apps/imports/models/import_map_set.py
# Created according to the user's permanent Copilot Base Instructions.

from __future__ import annotations
from django.db import models


class ImportMapSet(models.Model):
    """
    Head table for import mapping configurations.
    Defines which mapping applies to a supplier + source type,
    with a validity period.
    """

    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
        related_name="import_map_sets",
    )

    supplier = models.ForeignKey(
        "partners.Supplier",
        on_delete=models.PROTECT,
        related_name="import_map_sets",
    )

    source_type = models.ForeignKey(
        "imports.ImportSourceType",
        on_delete=models.PROTECT,
        related_name="import_map_sets",
        help_text="Import source type (e.g., file, API, CSV, Excel).",
    )

    description = models.CharField(max_length=255)

    valid_from = models.DateField(
        help_text="Date from which this mapping is valid."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Import Map Set"
        verbose_name_plural = "Import Map Sets"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "supplier", "source_type", "valid_from"],
                name="uq_mapset_org_supplier_type_validfrom",
            )
        ]

    def __str__(self) -> str:
        return f"{self.supplier.supplier_code} / {self.source_type.code} (from {self.valid_from})"
