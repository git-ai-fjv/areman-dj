#!/usr/bin/env python3
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations
from django.db import models


class State(models.Model):
    """State master data (single-letter code)."""

    state_code = models.CharField(
        max_length=1,
        primary_key=True,
        help_text="Single-letter state code.",
    )
    state_description = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional description/name of the state.",
    )

    class Meta:
        #db_table = "state"
        verbose_name = "State"
        verbose_name = "State"
        verbose_name_plural = "States"

    def __str__(self) -> str:
        return f"{self.state_code} — {self.state_description or 'State'}"

