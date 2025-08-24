# Created according to the user's Copilot Base Instructions.
"""
-- =========================
-- TABLE: tax_class
-- =========================
CREATE TABLE public.tax_class (
  id           INTEGER       PRIMARY KEY NOT NULL,
  name         VARCHAR(100)  NOT NULL,
  rate         NUMERIC(5,4)  NOT NULL,   -- z.B. 0.1900 (=19%)
  created_at   TIMESTAMPTZ   NOT NULL DEFAULT statement_timestamp(),
  updated_at   TIMESTAMPTZ   NOT NULL DEFAULT statement_timestamp(),
  CONSTRAINT uniq_tax_class_name UNIQUE (name),
  CONSTRAINT ck_tax_class_rate CHECK (rate >= 0 AND rate <= 1)
);
CREATE INDEX idx_tax_class_rate ON public.tax_class (rate);
"""
from __future__ import annotations

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.functions import Now
from django.db.models import Q


class TaxClass(models.Model):
    #id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    rate = models.DecimalField(
        max_digits=5, decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )

    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"{self.name} ({self.rate})"

    class Meta:
        db_table = "tax_class"
        indexes = [
            models.Index(fields=("rate",), name="idx_tax_class_rate"),
        ]
        constraints = [
            models.CheckConstraint(
                name="ck_tax_class_rate",
                check=Q(rate__gte=0) & Q(rate__lte=1),
            ),
        ]


