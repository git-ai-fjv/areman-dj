# apps/catalog/services/channel_variant_ops.py

# apps/catalog/services/channel_variant_ops.py
"""
Purpose:
    Service layer for managing ChannelVariant records. Provides a safe,
    reusable, and idempotent upsert interface for linking product variants
    to sales/distribution channels.

Context:
    A ChannelVariant represents the relationship between a sales channel
    (e.g., Webshop, Amazon) and a specific ProductVariant (SKU). It stores
    publishing state, external IDs, sync metadata, and activity flags.
    This service complements the seeding commands and is intended to be used
    by ETL jobs, admin features, or APIs.

Used by:
    - Import pipelines synchronizing product listings with external channels.
    - Admin operations or APIs that create/update channel listings.
    - Integration jobs that update publishing status or sync metadata.

Depends on:
    - apps.core.models.Organization
    - apps.catalog.models.Channel
    - apps.catalog.models.ProductVariant
    - apps.catalog.models.ChannelVariant

Key Features:
    - Atomic upsert by (organization, channel, variant).
    - Enforces required fields: org_code, channel_id, variant_id.
    - Supports optional flags and metadata:
        publish, is_active, need_shop_update,
        shop_product_id, shop_variant_id,
        last_synced_at, last_error, meta_json.
    - Raises ValidationError for missing required fields.

Example:
    >>> from apps.catalog.services.channel_variant_ops import upsert_channel_variant
    >>> payload = {
    ...     "org_code": 1,
    ...     "channel_id": 10,
    ...     "variant_id": 123,
    ...     "publish": True,
    ...     "is_active": True,
    ...     "need_shop_update": False,
    ...     "shop_product_id": "SKU-9999",
    ...     "shop_variant_id": "SKU-9999-V1",
    ...     "meta_json": {"synced_by": "import"},
    ... }
    >>> cv, created = upsert_channel_variant(payload)
    >>> print(cv.id, created)
"""


from __future__ import annotations

from typing import Dict, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.core.models.organization import Organization
from apps.catalog.models.channel import Channel
from apps.catalog.models.product_variant import ProductVariant
from apps.catalog.models.channel_variant import ChannelVariant


@transaction.atomic
def upsert_channel_variant(payload: Dict) -> Tuple[ChannelVariant, bool]:
    """
    Upsert a ChannelVariant via dict.

    Required: org_code, channel_id, variant_id
    Optional: publish, is_active, need_shop_update,
              shop_product_id, shop_variant_id,
              last_synced_at, last_error, meta_json

    Returns: (channel_variant, created)
    Raises: ValidationError, DoesNotExist, IntegrityError
    """
    required = ["org_code", "channel_id", "variant_id"]
    missing = [k for k in required if payload.get(k) in (None, "")]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    org = Organization.objects.get(org_code=int(payload["org_code"]))
    channel = Channel.objects.get(id=int(payload["channel_id"]))
    variant = ProductVariant.objects.get(id=int(payload["variant_id"]))

    defaults = {
        "publish": bool(payload.get("publish", False)),
        "is_active": bool(payload.get("is_active", True)),
        "need_shop_update": bool(payload.get("need_shop_update", False)),
        "shop_product_id": (payload.get("shop_product_id") or None),
        "shop_variant_id": (payload.get("shop_variant_id") or None),
        "last_synced_at": payload.get("last_synced_at"),
        "last_error": payload.get("last_error"),
        "meta_json": payload.get("meta_json"),
    }

    obj, created = ChannelVariant.objects.update_or_create(
        organization=org,
        channel=channel,
        variant=variant,
        defaults=defaults,
    )
    return obj, created

from apps.catalog.services.channel_variant_ops import upsert_channel_variant
#
# payload = {
#     "org_code": 1,
#     "channel_id": 10,
#     "variant_id": 123,
#     "publish": True,
#     "is_active": True,
#     "need_shop_update": False,
#     "shop_product_id": "SKU-9999",
#     "shop_variant_id": "SKU-9999-V1",
#     "last_error": None,
#     "meta_json": {"synced_by": "import", "note": "initial load"},
# }
#
# cv, created = upsert_channel_variant(payload)
# print(f"ChannelVariant: {cv}, created={created}")