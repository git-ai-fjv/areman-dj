#!/usr/bin/env python3
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations
from django.db import models


class Organization(models.Model):
    """Organization (Mandant) master data."""

    org_code = models.SmallIntegerField(
        primary_key=True,
        help_text="Business code for the organization (small integer).",
    )
    org_description = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional description/name of the organization.",
    )

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"

    def __str__(self) -> str:
        return f"{self.org_code} — {self.org_description or 'Organization'}"

