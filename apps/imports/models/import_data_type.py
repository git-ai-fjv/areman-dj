# apps/imports/models/import_data_type.py
"""
Purpose:
    Defines the available datatypes for mapping and transformation during imports.
    Ensures consistent typing when parsing external data sources into the system.

Context:
    Part of the `imports` app. Used by the import framework to validate and
    transform incoming values into the correct Python representation.

Fields:
    - code (CharField, 30, unique): Short code identifier (e.g., "str", "int", "decimal").
    - description (CharField, 100): Human-readable label for the type.
    - python_type (CharField, 50): Python type or handler string (e.g., "decimal.Decimal").

Relations:
    - No direct foreign keys. Acts as a reference/master table.

Used by:
    - Import pipeline and mapping services to resolve field datatypes.
    - Validation logic for ensuring correct type conversion.

Depends on:
    - Django ORM

Example:
    >>> from apps.imports.models import ImportDataType
    >>> t = ImportDataType.objects.create(
    ...     code="bool",
    ...     description="Boolean",
    ...     python_type="bool"
    ... )
    >>> print(t)
    bool (Boolean)
"""


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

