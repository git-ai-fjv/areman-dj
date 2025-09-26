# apps/imports/models/import_source_type.py
"""
Purpose:
    Defines available import source types (e.g., file, API, manual).
    Serves as a reference table for categorizing import runs and mappings.

Context:
    Part of the imports domain. Each ImportRun references an ImportSourceType
    to indicate where the data originated from. Used in mapping and logging.

Fields:
    - code (CharField, 20, unique): Short identifier (e.g., "file", "api").
    - description (CharField, 100): Human-readable description.

Relations:
    - ImportSourceType → multiple ImportRuns (1:n).
    - ImportSourceType → multiple ImportMapSets (1:n).

Used by:
    - ImportRun (source_type FK).
    - ImportMapSet (source_type FK).

Depends on:
    - Django ORM (constraints, unique checks).

Example:
    >>> from apps.imports.models import ImportSourceType
    >>> t = ImportSourceType.objects.create(code="file", description="File Import")
    >>> print(t)
    file — File Import
"""


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

