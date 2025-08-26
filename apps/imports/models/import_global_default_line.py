# apps/imports/models/import_global_default_line.py
# Created according to the user's permanent Copilot Base Instructions.

from __future__ import annotations
from django.db import models
from apps.imports.models.import_global_default_set import ImportGlobalDefaultSet


class ImportGlobalDefaultLine(models.Model):
    """
    Line items for global defaults.
    Each entry defines a target path and a default value.
    """

    set = models.ForeignKey(
        ImportGlobalDefaultSet,
        on_delete=models.CASCADE,
        related_name="glocal_default_lines",
    )

    target_path = models.CharField(max_length=255)
    default_value = models.JSONField(null=True, blank=True)
    transform = models.CharField(max_length=50, null=True, blank=True)
    is_required = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Import Global Default Line"
        verbose_name_plural = "Import Global Default Lines"

    def __str__(self) -> str:
        return f"{self.target_path} = {self.default_value}"

