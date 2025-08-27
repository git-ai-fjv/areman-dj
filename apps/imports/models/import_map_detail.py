# apps/imports/models/import_map_detail.py
# Created according to the user's permanent Copilot Base Instructions.

from __future__ import annotations
from django.db import models
from apps.imports.models.import_map_set import ImportMapSet


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
        return f"{self.source_path} → {self.target_path}"


