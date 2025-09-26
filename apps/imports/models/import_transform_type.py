# apps/imports/models/import_transform_type.py
"""
Purpose:
    Registry of supported transformation functions used in import mapping.
    Provides a unique code and description for each transform.

Context:
    Part of the imports domain. Transform types define how raw values
    from import payloads should be processed before saving.

Fields:
    - code (CharField, 50, unique): Identifier of the transform (e.g., "uppercase", "int").
    - description (CharField, 255): Human-readable description of the transformation.

Relations:
    - ImportTransformType → multiple ImportGlobalDefaultLines (1:n).
    - ImportTransformType → used in mapping definitions (FKs).

Used by:
    - ImportGlobalDefaultLine (transform FK).
    - Mapping and ETL logic to dynamically apply transforms.

Depends on:
    - Django ORM.

Example:
    >>> from apps.imports.models import ImportTransformType
    >>> t = ImportTransformType.objects.create(code="uppercase", description="Convert text to upper case")
    >>> print(t)
    uppercase — Convert text to upper case
"""


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

