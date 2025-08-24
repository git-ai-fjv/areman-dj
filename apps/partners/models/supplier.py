# apps/partners/models/supplier.py
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations

from django.db import models
from django.db.models.functions import Now


class Supplier(models.Model):
    """Supplier master data, scoped by organization (org_code)."""

    # PK BIGINT
    #id = models.BigAutoField(primary_key=True)

    # FK zu core.Organization(org_code); DB column bleibt 'org_code'
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,  # ON DELETE RESTRICT
        related_name="suppliers",
    )

    supplier_code = models.CharField(
        max_length=20,
    )
    is_active = models.BooleanField(
        default=True,
    )
    supplier_description = models.CharField(
        max_length=200,
        blank=True,
        default="",
    )

    # --- Common supplier fields (all optional; appended to preserve order) ---
    contact_name = models.CharField(
        max_length=100, blank=True, default="", help_text="Primary contact person name."
    )
    email = models.CharField(
        max_length=200, blank=True, default="", help_text="Contact email address."
    )  # Use CharField to avoid DB-specific validators for now.
    phone = models.CharField(
        max_length=50, blank=True, default="", help_text="Primary phone number."
    )
    website = models.CharField(
        max_length=200, blank=True, default="", help_text="Website URL."
    )
    tax_id = models.CharField(
        max_length=50, blank=True, default="", help_text="Tax/VAT identifier."
    )
    address_line1 = models.CharField(
        max_length=200, blank=True, default="", help_text="Address line 1."
    )
    address_line2 = models.CharField(
        max_length=200, blank=True, default="", help_text="Address line 2."
    )
    postal_code = models.CharField(
        max_length=20, blank=True, default="", help_text="Postal/ZIP code."
    )
    city = models.CharField(
        max_length=100, blank=True, default="", help_text="City."
    )
    country_code = models.CharField(
        max_length=2, blank=True, default="", help_text="ISO 3166-1 alpha-2 country code."
    )
    payment_terms = models.CharField(
        max_length=50, blank=True, default="", help_text="Payment terms shorthand (e.g., NET30)."
    )
    is_preferred = models.BooleanField(
        default=False, help_text="Mark as preferred supplier."
    )
    lead_time_days = models.SmallIntegerField(
        default=0, help_text="Typical lead time in days."
    )

    # Timestamps for parity with other tables
    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"{self.supplier_code} — {self.supplier_description or 'Supplier'}"

    class Meta:
        # db_table = "supplier"
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"
        # indexes = [
        #     models.Index(fields=["organization"], name="idx_supplier_org"),
        # ]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "supplier_code"],
                name="uniq_supplier_org_code",
            ),
            models.UniqueConstraint(
                fields=["organization", "id"],
                name="uniq_supplier_org_id",
            ),
        ]
