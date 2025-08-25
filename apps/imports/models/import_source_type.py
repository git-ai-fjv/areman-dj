# apps/imports/models/import_source_type.py
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations
from django.db import models


class ImportSourceType(models.Model):
    """
    Reference table for different import source types
    (e.g., file, API, manual, other).
    """

    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Short machine-readable code (e.g., 'file', 'api')."
    )
    description = models.CharField(
        max_length=100,
        help_text="Human-readable description of the source type."
    )

    class Meta:
        verbose_name = "Import Source Type"
        verbose_name_plural = "Import Source Types"

    def __str__(self) -> str:
        return f"{self.code} — {self.description}"

