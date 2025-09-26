# apps/partners/models/supplier.py
"""
Purpose:
    Represents supplier master data within an organization.
    Each supplier is uniquely identified by a supplier code and
    may include commercial, contact, and logistical information.

Context:
    Part of the partners app. Suppliers are organizationally scoped
    entities used for procurement, import mapping, and integrations.

Fields:
    - organization (FK → core.Organization): Owning organization.
    - supplier_code (CharField, 20): Unique supplier code per organization.
    - is_active (BooleanField): Whether the supplier is active.
    - supplier_description (CharField, 200): Optional description/name.
    - contact_name (CharField, 100): Primary contact person.
    - email (CharField, 200): Contact email address.
    - phone (CharField, 50): Primary phone number.
    - website (CharField, 200): Website URL.
    - tax_id (CharField, 50): Tax/VAT identifier.
    - address_line1 (CharField, 200): Address line 1.
    - address_line2 (CharField, 200): Address line 2.
    - postal_code (CharField, 20): Postal/ZIP code.
    - city (CharField, 100): City name.
    - country_code (CharField, 2): ISO 3166-1 alpha-2 code.
    - payment_terms (CharField, 50): Payment term shorthand (e.g., NET30).
    - is_preferred (BooleanField): Whether marked as preferred supplier.
    - lead_time_days (SmallIntegerField): Typical lead time in days.
    - comment (CharField, 200): Optional internal comment.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Organization → multiple Suppliers

Used by:
    - Procurement workflows
    - Import mapping (apps/imports)
    - Inventory and purchase order processing

Depends on:
    - apps.core.models.Organization
    - Django ORM

Example:
    >>> from apps.partners.models import Supplier
    >>> s = Supplier.objects.create(
    ...     organization=org,
    ...     supplier_code="SUP001",
    ...     supplier_description="MegaParts Ltd.",
    ...     email="sales@megaparts.com"
    ... )
    >>> print(s)
    SUP001 — MegaParts Ltd.
"""


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
    comment = models.CharField(
        max_length=200, blank=True, default="", help_text="comment"
    )  # Keep CharField for cross-DB portability; can switch to EmailField later.


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
