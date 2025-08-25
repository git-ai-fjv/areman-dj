# apps/pricing/services/price_list_ops.py
# Created according to the user's Copilot Base Instructions.

from __future__ import annotations

from typing import Dict, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.core.models.organization import Organization
from apps.core.models.currency import Currency
from apps.pricing.models.price_list import PriceList


@transaction.atomic
def upsert_price_list(payload: Dict) -> Tuple[PriceList, bool]:
    """
    Upsert a PriceList via dict.

    Required: org_code, price_list_code, kind, currency_code
    Optional: price_list_description, is_active (bool)

    Returns: (price_list, created)
    Raises: ValidationError, DoesNotExist, IntegrityError
    """
    required = ["org_code", "price_list_code", "kind", "currency_code"]
    missing = [k for k in required if payload.get(k) in (None, "")]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    org = Organization.objects.get(org_code=payload["org_code"])
    currency = Currency.objects.get(code=payload["currency_code"])  # <-- FIX

    defaults = {
        "price_list_description": payload.get("price_list_description", ""),
        "kind": payload["kind"],
        "currency": currency,
        "is_active": bool(payload.get("is_active", True)),
    }

    obj, created = PriceList.objects.update_or_create(
        organization=org,
        price_list_code=payload["price_list_code"],
        defaults=defaults,
    )
    return obj, created
