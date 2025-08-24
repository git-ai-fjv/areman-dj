#!/usr/bin/env python3
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations
from django.db import models


class Origin(models.Model):
    """Origin master data (single-letter code)."""

    origin_code = models.CharField(
        max_length=1,
        primary_key=True,
        help_text="Single-letter origin code.",
    )
    origin_description = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional description/name of the origin.",
    )

    class Meta:
        #db_table = "origin"
        verbose_name = "Origin"
        verbose_name_plural = "Origins"

    def __str__(self) -> str:
        return f"{self.origin_code} — {self.origin_description or 'Origin'}"

