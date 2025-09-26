# apps/imports/models/import_map_set.py
"""
Purpose:
    Represents a configuration set that defines how raw import data from a
    supplier and source type should be mapped into the ERP structure.

Context:
    Part of the imports domain. Each ImportMapSet groups multiple
    ImportMapDetail entries that specify field-level mapping rules.
    Defines which mapping applies for a given supplier and source type,
    with a start date of validity.

Fields:
    - organization (FK → core.Organization): The organization this mapping belongs to.
    - supplier (FK → partners.Supplier): The supplier providing the import data.
    - source_type (FK → imports.ImportSourceType): The type of import source (file, API, etc.).
    - description (CharField, 255): Human-readable description of the mapping set.
    - valid_from (DateField): Date from which this mapping is effective.
    - created_at (DateTimeField): Timestamp when the mapping set was created.

Relations:
    - Organization → multiple ImportMapSet
    - Supplier → multiple ImportMapSet
    - ImportSourceType → multiple ImportMapSet
    - ImportMapSet → multiple ImportMapDetail (child rules)

Used by:
    - Import processing engine to determine which mapping rules to apply
      for supplier imports.
    - apps.imports.models.import_map_detail.ImportMapDetail

Depends on:
    - apps.core.models.Organization
    - apps.partners.models.Supplier
    - apps.imports.models.import_source_type.ImportSourceType

Example:
    >>> from apps.imports.models import ImportMapSet
    >>> ms = ImportMapSet.objects.create(
    ...     organization=org,
    ...     supplier=supplier,
    ...     source_type=src_type,
    ...     description="Default CSV mapping",
    ...     valid_from="2025-01-01",
    ... )
    >>> print(ms)
    SUPP01 / file (from 2025-01-01)
"""

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
