# apps/imports/models/import_global_default_set.py
# Created according to the user's permanent Copilot Base Instructions.

from __future__ import annotations
from django.db import models


class ImportGlobalDefaultSet(models.Model):
    """
    Head table for global defaults that apply to all suppliers.
    Each set has a validity period and a description.
    """

    description = models.CharField(max_length=255)
    valid_from = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Import Global Default Set"
        verbose_name_plural = "Import Global Default Sets"

    def __str__(self) -> str:
        return f"{self.description} (from {self.valid_from})"

