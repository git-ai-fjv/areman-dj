# Created according to the user's Copilot Base Instructions.
"""
-- =========================
-- TABLE: currency_rate
-- =========================
CREATE TABLE public.currency_rate (
  id          BIGSERIAL     PRIMARY KEY NOT NULL,
  base_code   CHAR(3)       NOT NULL,   -- FK -> currency(code)
  quote_code  CHAR(3)       NOT NULL,   -- FK -> currency(code)
  rate        NUMERIC(16,8) NOT NULL,   -- z.B. 1.12345678
  rate_date   DATE          NOT NULL,   -- Kurs-Datum
  created_at  TIMESTAMPTZ   NOT NULL DEFAULT statement_timestamp(),
  updated_at  TIMESTAMPTZ   NOT NULL DEFAULT statement_timestamp(),
  FOREIGN KEY (base_code)  REFERENCES public.currency (code) ON DELETE NO ACTION,
  FOREIGN KEY (quote_code) REFERENCES public.currency (code) ON DELETE NO ACTION,
  CONSTRAINT ck_currency_rate_positive CHECK (rate > 0),
  CONSTRAINT uniq_currency_rate UNIQUE (base_code, quote_code, rate_date)
);
CREATE INDEX idx_currency_rate_date       ON public.currency_rate (rate_date);
CREATE INDEX idx_currency_rate_base_quote ON public.currency_rate (base_code, quote_code);
"""
from __future__ import annotations

from django.db import models
from django.core.validators import MinValueValidator
from django.db.models.functions import Now
from django.db.models import Q


class CurrencyRate(models.Model):
    #id = models.BigAutoField(primary_key=True)

    base = models.ForeignKey(
        "core.Currency",
        on_delete=models.PROTECT,
        related_name="base_rates",
    )
    quote = models.ForeignKey(
        "core.Currency",
        on_delete=models.PROTECT,
        related_name="quote_rates",
    )

    rate = models.DecimalField(max_digits=16, decimal_places=8, validators=[MinValueValidator(0.00000001)])
    rate_date = models.DateField()

    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"{self.base_id}/{self.quote_id} @ {self.rate} ({self.rate_date})"

    class Meta:
        #db_table = "currency_rate"
        # indexes = [
        #     models.Index(fields=("rate_date",), name="idx_currency_rate_date"),
        #     models.Index(fields=("base", "quote"), name="idx_currency_rate_base_quote"),
        # ]
        constraints = [
            models.UniqueConstraint(
                fields=("base", "quote", "rate_date"),
                name="uniq_currency_rate",
            ),
            models.CheckConstraint(
                name="ck_currency_rate_positive",
                check=Q(rate__gt=0),
            ),
        ]
