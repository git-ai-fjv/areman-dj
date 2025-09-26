# apps/core/models/organization.py
"""
Purpose:
    Master data table for organizations (tenants/mandants).
    Provides a scoped context for all other business entities.

Context:
    Every business object (customer, supplier, product, pricing, etc.)
    is linked to an Organization via org_code.

Fields:
    - org_code (SmallInteger, PK): Unique code identifying the organization.
    - org_description (CharField): Optional description/name.

Constraints:
    - org_code is the primary key.
    - No additional constraints defined.

Example:
    >>> from apps.core.models import Organization
    >>> org = Organization.objects.create(org_code=1, org_description="Main Company")
    >>> str(org)
    'Main Company'
"""


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
        return f"{self.org_description or 'Organization'}"

