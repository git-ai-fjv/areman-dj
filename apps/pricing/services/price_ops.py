# apps/pricing/services/price_ops.py
# Created according to the user's Copilot Base Instructions.

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
