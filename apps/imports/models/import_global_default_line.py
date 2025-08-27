# apps/imports/models/import_global_default_line.py

from __future__ import annotations
from django.db import models
from apps.imports.models.import_global_default_set import ImportGlobalDefaultSet
from apps.imports.models.import_data_type import ImportDataType
from apps.imports.models.import_transform_type import ImportTransformType


class ImportGlobalDefaultLine(models.Model):
    """
    Line items for global defaults.
    Each entry defines a target path and a default value.
    """

    set = models.ForeignKey(
        ImportGlobalDefaultSet,
        on_delete=models.CASCADE,
        related_name="global_default_lines",
    )

    target_path = models.CharField(max_length=255)
    default_value = models.JSONField(null=True, blank=True)

    # statt CharField → FK
    transform = models.ForeignKey(
        ImportTransformType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="default_lines",
        help_text="Transform to apply to this field (FK instead of free text).",
    )

    is_required = models.BooleanField(default=False)

    target_datatype = models.ForeignKey(
        ImportDataType,
        on_delete=models.PROTECT,
        related_name="default_lines",
        help_text="Datatype for this default value (e.g., str, int, decimal)."
    )

    class Meta:
        verbose_name = "Import Global Default Line"
        verbose_name_plural = "Import Global Default Lines"
        constraints = [
            models.UniqueConstraint(
                fields=["set", "target_path"],
                name="uq_globaldefaultline_set_target"
            )
        ]

    def __str__(self) -> str:
        return f"{self.target_path} = {self.default_value}"
