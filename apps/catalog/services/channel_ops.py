# apps/catalog/services/channel_ops.py
# Created according to the user's Copilot Base Instructions.
from __future__ import annotations
from typing import Dict, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.core.models.organization import Organization
from apps.core.models.currency import Currency
from apps.catalog.models.channel import Channel


@transaction.atomic
def upsert_channel(payload: Dict) -> Tuple[Channel, bool]:
    """
    Upsert Channel by (organization, channel_code).
    Required: org_code, channel_code, channel_name, base_currency_code
    Optional: kind, is_active
    """
    required = ["org_code", "channel_code", "channel_name", "base_currency_code"]
    missing = [k for k in required if payload.get(k) in (None, "")]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    org = Organization.objects.get(org_code=int(payload["org_code"]))
    curr = Currency.objects.get(code=str(payload["base_currency_code"]).upper())

    obj, created = Channel.objects.update_or_create(
        organization=org,
        channel_code=str(payload["channel_code"])[:20],
        defaults={
            "channel_name": str(payload["channel_name"])[:200],
            "kind": str(payload.get("kind", "shop"))[:20],
            "base_currency": curr,
            "is_active": bool(payload.get("is_active", True)),
        },
    )
    return obj, created
#
# from apps.catalog.services.channel_ops import upsert_channel
# ch, created = upsert_channel({"org_code": 1, "channel_code": "WEB", "channel_name": "Webshop", "base_currency_code": "EUR"})
# print(ch.id, created)

