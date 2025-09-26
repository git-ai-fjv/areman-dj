# apps/imports/models/import_global_default_set.py
"""
Purpose:
    Represents the head record for global default configurations that apply
    to all suppliers within an organization. Each set has a description and
    validity date that determines which defaults are active at a given time.

Context:
    Part of the imports domain. Used as a container for multiple
    ImportGlobalDefaultLine entries that define specific default values.
    Provides versioning of defaults by validity period.

Fields:
    - organization (FK → core.Organization): Owner of the default set.
    - description (CharField, 255): Human-readable description.
    - valid_from (DateField): Start date from which the defaults are active.
    - created_at (DateTimeField): Timestamp when the set was created.

Relations:
    - Organization → multiple ImportGlobalDefaultSet
    - ImportGlobalDefaultSet → multiple ImportGlobalDefaultLine

Used by:
    - apps/imports/services/defaults.py (get_active_default_set, build_base_dict)

Depends on:
    - apps.core.models.Organization
    - apps.imports.models.import_global_default_line.ImportGlobalDefaultLine

Example:
    >>> from apps.imports.models import ImportGlobalDefaultSet
    >>> default_set = ImportGlobalDefaultSet.objects.create(
    ...     organization=org,
    ...     description="Default product values",
    ...     valid_from="2025-01-01",
    ... )
    >>> print(default_set)
    Default product values (from 2025-01-01)
"""


from __future__ import annotations
from django.db import models


class ImportGlobalDefaultSet(models.Model):
    """
    Head table for global defaults that apply to all suppliers.
    Each set has a validity period and a description.
    """
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
        related_name="global_default_sets",
    )

    description = models.CharField(max_length=255)
    valid_from = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Import Global Default Set"
        verbose_name_plural = "Import Global Default Sets"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "valid_from"],
                name="uq_globaldefaultset_org_validfrom",
            )
        ]

    def __str__(self) -> str:
        return f"{self.description} (from {self.valid_from})"
