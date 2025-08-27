# apps/imports/models/import_transform_type.py
# Created according to the user's permanent Copilot Base Instructions.

from __future__ import annotations
from django.db import models


class ImportTransformType(models.Model):
    """
    Central registry for all supported transforms.
    Example: uppercase, lowercase, strip, int, decimal, bool
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique code for this transform (e.g., uppercase, int, bool).",
    )
    description = models.CharField(
        max_length=255,
        help_text="Human-readable description of what this transform does.",
    )

    class Meta:
        verbose_name = "Import Transform Type"
        verbose_name_plural = "Import Transform Types"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} — {self.description}"

