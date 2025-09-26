# apps/partners/models/customer.py
#!/usr/bin/env python3
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations

from django.db import models
from django.db.models.functions import Now


class Customer(models.Model):
    """Customer master data, scoped by organization (org_code)."""

    #id = models.BigAutoField(primary_key=True)

    # FK to core.Organization(org_code); DB column stays 'org_code'
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,  # ON DELETE RESTRICT
        related_name="customers",
    )

    customer_code = models.CharField(
        max_length=20,
        help_text="Customer code (unique within organization).",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the customer is active.",
    )
    customer_description = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Optional description/name of the customer.",
    )

    # --- Common customer fields (all optional; appended to preserve order) ---
    contact_name = models.CharField(
        max_length=100, blank=True, default="", help_text="Primary contact person name."
    )
    email = models.CharField(
        max_length=200, blank=True, default="", help_text="Contact email address."
    )  # Keep CharField for cross-DB portability; can switch to EmailField later.
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
    comment = models.CharField(
        max_length=200, blank=True, default="", help_text="comment"
    )  # Keep CharField for cross-DB portability; can switch to EmailField later.

    # Timestamps to match project standard (DB defaults via NOW())
    created_at = models.DateTimeField(db_default=Now(), editable=False)
    updated_at = models.DateTimeField(db_default=Now(), editable=False)

    def __str__(self) -> str:
        return f"{self.customer_code} — {self.customer_description or 'Customer'}"

    class Meta:
        # db_table = "customer"
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        # indexes = [
        #     models.Index(fields=["organization"], name="idx_customer_org"),
        #     models.Index(fields=["is_active"], name="idx_customer_active"),
        # ]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "customer_code"],
                name="uniq_customer_org_code",
            ),
            models.UniqueConstraint(
                fields=["organization", "id"],
                name="uniq_customer_org_id",
            ),
        ]
