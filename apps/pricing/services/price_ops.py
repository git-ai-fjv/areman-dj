# apps/pricing/services/price_ops.py
"""
Purpose:
    Service layer providing operations for creating or updating
    SalesChannelVariantPrice records from dictionary payloads.
    Handles validation, foreign key resolution, and timezone safety.

Context:
    Part of the `apps.pricing` app. Centralizes price handling logic
    for sales channel variants to keep management commands and APIs lean.

Used by:
    - Import and synchronization jobs that assign prices to channel variants
    - Management commands or services that need to update prices in bulk

Depends on:
    - apps.core.models.Organization
    - apps.pricing.models.PriceList
    - apps.catalog.models.ChannelVariant
    - apps.pricing.models.SalesChannelVariantPrice
    - Django transaction management and timezone utilities

Example:
    from apps.pricing.services.price_ops import upsert_sales_channel_variant_price
    from datetime import datetime

    payload = {
        "org_code": 1,
        "price_list_id": 10,
        "channel_variant_id": 42,
        "valid_from": datetime(2025, 1, 1, 0, 0),
        "price": "19.99",
        "need_update": True,
    }
    scvp, created = upsert_sales_channel_variant_price(payload)
    print(scvp, created)
"""

from __future__ import annotations

from typing import Dict, Tuple
from datetime import datetime

from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.timezone import is_naive, make_aware, get_current_timezone

from apps.core.models.organization import Organization
from apps.pricing.models.price_list import PriceList
from apps.catalog.models.channel_variant import ChannelVariant
from apps.pricing.models.sales_channel_variant_price import SalesChannelVariantPrice


@transaction.atomic
def upsert_sales_channel_variant_price(payload: Dict) -> Tuple[SalesChannelVariantPrice, bool]:
    """
    Upsert a SalesChannelVariantPrice via dict.

    Required: org_code, price_list_id, channel_variant_id, valid_from, price
    Optional: valid_to, need_update (bool)

    Returns: (sales_channel_variant_price, created)
    Raises: ValidationError, DoesNotExist, IntegrityError
    """
    required = ["org_code", "price_list_id", "channel_variant_id", "valid_from", "price"]
    missing = [k for k in required if payload.get(k) in (None, "")]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    org = Organization.objects.get(org_code=int(payload["org_code"]))
    price_list = PriceList.objects.get(id=int(payload["price_list_id"]))
    channel_variant = ChannelVariant.objects.get(id=int(payload["channel_variant_id"]))

    # Ensure valid_from is tz-aware
    valid_from = payload["valid_from"]
    if isinstance(valid_from, datetime) and is_naive(valid_from):
        valid_from = make_aware(valid_from, get_current_timezone())

    # Ensure valid_to is tz-aware if present
    valid_to = payload.get("valid_to")
    if isinstance(valid_to, datetime) and is_naive(valid_to):
        valid_to = make_aware(valid_to, get_current_timezone())

    defaults = {
        "price": payload["price"],
        "valid_to": valid_to,
        "need_update": bool(payload.get("need_update", False)),
    }

    obj, created = SalesChannelVariantPrice.objects.update_or_create(
        organization=org,
        price_list=price_list,
        channel_variant=channel_variant,
        valid_from=valid_from,
        defaults=defaults,
    )
    return obj, created
