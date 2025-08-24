#!/usr/bin/env python3
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations
from django.db import models


class Manufacturer(models.Model):
    """Manufacturer master data (brand/vendor entity for catalog)."""

    manufacturer_code = models.SmallIntegerField(
        primary_key=True,
        help_text="Business code for the manufacturer (small integer).",
    )
    manufacturer_description = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional description/name of the manufacturer.",
    )

    class Meta:
        #db_table = "manufacturer"
        verbose_name = "Manufacturer"
        verbose_name_plural = "Manufacturers"

    def __str__(self) -> str:
        return (
            f"{self.manufacturer_code} — "
            f"{self.manufacturer_description or 'Manufacturer'}"
        )
