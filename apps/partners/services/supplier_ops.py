# apps/partners/services/supplier_ops.py
"""
Purpose:
    Service functions to upsert (create or update) Supplier records in the database.
    Encapsulates supplier persistence logic in a reusable API for other services.

Context:
    Located in `apps.partners.services`. Provides write-access operations on the
    Supplier model, independent of management commands or imports.

Used by:
    - Seed commands (e.g., `seed_suppliers`)
    - Import services or pipelines that create/update suppliers
    - Potential API endpoints for supplier administration

Depends on:
    - apps.core.models.Organization
    - apps.partners.models.Supplier
    - Django transaction management and ValidationError

Example:
    from apps.partners.services.supplier_ops import upsert_supplier

    payload = {
        "org_code": 1,
        "supplier_code": "SUP-1001",
        "supplier_description": "Main Widgets Supplier",
        "email": "contact@widgets.example",
        "phone": "+49-123-456789",
        "is_preferred": True,
        "lead_time_days": 14,
    }
    supplier, created = upsert_supplier(payload)
    print(f"Supplier: {supplier}, created={created}")
"""


from __future__ import annotations

from typing import Dict, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.core.models.organization import Organization
from apps.partners.models.supplier import Supplier


@transaction.atomic
def upsert_supplier(payload: Dict) -> Tuple[Supplier, bool]:
    """
    Upsert a Supplier via dict.

    Required: org_code, supplier_code
    Optional: is_active, supplier_description, contact_name, email, phone, website,
              tax_id, address_line1, address_line2, postal_code, city, country_code,
              payment_terms, is_preferred, lead_time_days

    Returns: (supplier, created)
    Raises: ValidationError, DoesNotExist, IntegrityError
    """
    required = ["org_code", "supplier_code"]
    missing = [k for k in required if payload.get(k) in (None, "")]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    org = Organization.objects.get(org_code=int(payload["org_code"]))

    defaults = {
        "is_active": bool(payload.get("is_active", True)),
        "supplier_description": payload.get("supplier_description", ""),
        "contact_name": payload.get("contact_name", ""),
        "email": payload.get("email", ""),
        "phone": payload.get("phone", ""),
        "website": payload.get("website", ""),
        "tax_id": payload.get("tax_id", ""),
        "address_line1": payload.get("address_line1", ""),
        "address_line2": payload.get("address_line2", ""),
        "postal_code": payload.get("postal_code", ""),
        "city": payload.get("city", ""),
        "country_code": payload.get("country_code", ""),
        "payment_terms": payload.get("payment_terms", ""),
        "is_preferred": bool(payload.get("is_preferred", False)),
        "lead_time_days": int(payload.get("lead_time_days", 0)),
    }

    obj, created = Supplier.objects.update_or_create(
        organization=org,
        supplier_code=payload["supplier_code"],
        defaults=defaults,
    )
    return obj, created

# from apps.partners.services.supplier_ops import upsert_supplier
#
# payload = {
#     "org_code": 1,
#     "supplier_code": "SUP-1001",
#     "supplier_description": "Main Widgets Supplier",
#     "email": "contact@widgets.example",
#     "phone": "+49-123-456789",
#     "is_preferred": True,
#     "lead_time_days": 14,
# }
#
# supplier, created = upsert_supplier(payload)
# print(f"Supplier: {supplier}, created={created}")


