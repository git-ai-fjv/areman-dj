# apps/imports/models/import_data_type.py
# Created according to the user's permanent Copilot Base Instructions.

from __future__ import annotations
from django.db import models


class ImportDataType(models.Model):
    """
    Defines available datatypes for mapping transformations.
    Examples: string, integer, decimal, boolean, date, datetime, json.
    """

    code = models.CharField(
        max_length=30,
        unique=True,
        help_text="Short code identifier (e.g., 'str', 'int', 'decimal', 'bool').",
    )

    description = models.CharField(
        max_length=100,
        help_text="Human-readable description (e.g., 'String', 'Integer').",
    )

    python_type = models.CharField(
        max_length=50,
        help_text="Target Python type or handler (e.g., 'str', 'int', 'decimal.Decimal').",
    )

    class Meta:
        verbose_name = "Import Data Type"
        verbose_name_plural = "Import Data Types"

    def __str__(self) -> str:
        return f"{self.code} ({self.description})"

