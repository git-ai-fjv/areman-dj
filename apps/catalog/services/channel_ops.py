# apps/catalog/services/channel_ops.py

"""
Purpose:
    Service layer for managing Channel records in a safe, reusable way.
    Provides an atomic upsert operation that ensures consistency across
    organizations and currencies.

Context:
    Channels represent sales or distribution endpoints (e.g., Webshop, Amazon,
    Point of Sale) and are always scoped to an organization with a base
    currency. This service is the programmatic counterpart to the seeding
    commands and is designed for use by other services, views, or ETL jobs.

Used by:
    - Import/ETL jobs synchronizing external channel definitions.
    - Admin features or APIs that create or update channels dynamically.
    - Test fixtures or bootstrap scripts needing idempotent channel setup.

Depends on:
    - apps.core.models.Organization
    - apps.core.models.Currency
    - apps.catalog.models.Channel

Key Features:
    - Idempotent upsert by (organization, channel_code).
    - Enforces required fields: org_code, channel_code, channel_name,
      base_currency_code.
    - Validates references to Organization and Currency.
    - Supports optional fields: kind (default "shop"), is_active (default True).
    - Trims string lengths to model constraints.

Example:
    >>> from apps.catalog.services.channel_ops import upsert_channel
    >>> ch, created = upsert_channel({
    ...     "org_code": 1,
    ...     "channel_code": "WEB",
    ...     "channel_name": "Webshop",
    ...     "base_currency_code": "EUR"
    ... })
    >>> print(ch.id, created)  # channel primary key, created=True/False
"""

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

