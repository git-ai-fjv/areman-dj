# apps/imports/models/import_map_detail.py
"""
Purpose:
    Represents a single mapping rule that defines how a field from the source
    import payload is transformed and assigned to a standardized target path.

Context:
    Part of the imports domain. Each ImportMapDetail belongs to an
    ImportMapSet, forming a collection of rules that describe how to
    process supplier or external data into the ERP structure.

Fields:
    - map_set (FK → ImportMapSet): Parent set grouping related map details.
    - source_path (CharField, 255): Path of the source field in the raw payload.
    - target_path (CharField, 255): Path in the standardized dict where the
      value will be stored.
    - target_datatype (FK → ImportDataType): Datatype the value should be
      converted to.
    - transform (CharField, 50, nullable): Optional transformation to apply
      (e.g., uppercase, decimal).
    - is_required (BooleanField): Marks if the target field is mandatory.

Relations:
    - ImportMapSet → multiple ImportMapDetail
    - ImportDataType → multiple ImportMapDetail

Used by:
    - Import processing pipeline to transform raw supplier data.
    - apps.imports.services.transform_utils.apply_transform

Depends on:
    - apps.imports.models.import_map_set.ImportMapSet
    - apps.imports.models.import_data_type.ImportDataType

Example:
    >>> from apps.imports.models import ImportMapDetail, ImportMapSet, ImportDataType
    >>> dt = ImportDataType.objects.get(code="decimal")
    >>> ms = ImportMapSet.objects.first()
    >>> detail = ImportMapDetail.objects.create(
    ...     map_set=ms,
    ...     source_path="Listenpreis",
    ...     target_path="price.price",
    ...     target_datatype=dt,
    ...     transform="decimal",
    ...     is_required=True,
    ... )
    >>> print(detail)
    Listenpreis → price.price (decimal)
"""

from __future__ import annotations
from django.db import models
from apps.imports.models.import_map_set import ImportMapSet
from apps.imports.models.import_data_type import ImportDataType


class ImportMapDetail(models.Model):
    """
    Line items for import mapping.
    Each entry defines how to map a field from the source payload
    to a target path in the standardized dict.
    """

    map_set = models.ForeignKey(
        ImportMapSet,
        on_delete=models.CASCADE,
        related_name="map_details",
    )

    source_path = models.CharField(
        max_length=255,
        help_text="Path in the source payload (e.g., 'translated.name', 'Artikelnummer').",
    )

    target_path = models.CharField(
        max_length=255,
        help_text="Path in the standardized dict (e.g., 'product.name', 'price.price').",
    )

    target_datatype = models.ForeignKey(
        ImportDataType,
        on_delete=models.PROTECT,
        related_name="map_details",
        help_text="Datatype the target value should be converted to.",
    )

    transform = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Optional transform function to apply (e.g., 'upper', 'decimal').",
    )

    is_required = models.BooleanField(
        default=False,
        help_text="If true, the target field must be present after mapping.",
    )

    class Meta:
        verbose_name = "Import Map Detail"
        verbose_name_plural = "Import Map Details"
        constraints = [
            models.UniqueConstraint(
                fields=["map_set", "source_path", "target_path"],
                name="uq_mapdetail_set_source_target",
            )
        ]

    def __str__(self) -> str:
        return f"{self.source_path} → {self.target_path} ({self.target_datatype.code})"
