# apps/core/models/currency.py
# Created according to the user's Copilot Base Instructions.



from __future__ import annotations

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.functions import Now


class Currency(models.Model):
    """ISO-4217 Währungen mit Anzeige-Infos und Aktiv-Flag."""

    # code CHAR(3) PRIMARY KEY
    code = models.CharField(primary_key=True, max_length=3)

    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=8, null=True, blank=True)

    # 0..6 (EUR=2) – validieren in App + DB
    decimal_places = models.SmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(6)]
    )

    is_active = models.BooleanField(default=True)

    # DB setzt Timestamps (keine auto_now*; wir spiegeln nur die Spalten)
    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


