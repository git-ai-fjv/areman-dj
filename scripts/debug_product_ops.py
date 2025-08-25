#!/usr/bin/env python3
# scripts/debug_product_ops.py
# Created according to the user's Copilot Base Instructions.
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

#from django.contrib.gis.gdal.prototypes.geom import ogr_crosses
from django.db import connection

# 🔌 Bootstrap Django environment
import scripts.bootstrap_django  # noqa: F401

# with connection.cursor() as cursor:
#     cursor.execute("select current_database(), current_user, current_schema();")
#     print("Runtime DB info:", cursor.fetchall())

from apps.catalog.services.channel_ops import upsert_channel
from apps.catalog.services.product_ops import upsert_product
from apps.catalog.services.variant_ops import upsert_variant
from apps.pricing.services.price_list_ops import upsert_price_list
from apps.catalog.services.channel_variant_ops import upsert_channel_variant
from apps.pricing.services.price_ops import upsert_sales_channel_variant_price
from apps.partners.services.supplier_ops import upsert_supplier
from apps.procurement.services.supplier_product_ops import upsert_supplier_product


org_code = 1  # Default organization code for testing

if __name__ == "__main__":

    payload_channel = {
        "org_code": org_code,
        "channel_code": "WEB",
        "channel_name": "Webshop",
        "base_currency_code": "EUR",
    }


    ch, created = upsert_channel(payload_channel)
    print(f"{ch.pk = } Product: {ch}, created={created}")

    payload_product = {
        "org_code": org_code,
        "manufacturer_code": 1,
        "manufacturer_part_number": "ZX-91",
        "name": "Widget ZX-91",
        "slug": "widget-zx-91",
        "product_group_code": "1",
        "is_active": True,
    }

    p, created = upsert_product(payload_product)

    print(f"{p.pk = } Product: {p}, created={created}")
    payload_variant = {
        "org_code": org_code,
        "product_id": p.pk,
            "origin_code": "E",
            "state_code": "N",
            "packing_code": "1",
            "weight": "0.250",
    }
    v, created = upsert_variant(payload_variant)
    print(f"{v.pk = } Variant: {v}, created={created}")

    payload_price_list = {
        "org_code": org_code,
        "price_list_code": "S1",
        "kind": "S",  # 'S' for sales, 'P' for purchase
        "currency_code": "EUR",
        "price_list_description": "Standard Sales Pricelist",
        "is_active": True,
    }
    pl, created = upsert_price_list(payload_price_list)
    print(f"PriceList: {pl}, created={created}")

# Connect the variant to the channel and price list with a price

    channel_variant_payload = {
        "org_code": org_code,
        "channel_id": ch.pk,
        "variant_id": v.pk,
        "publish": True,
        "is_active": True,
        "need_shop_update": False,
        "shop_product_id": "SKU-9999",
        "shop_variant_id": "SKU-9999-V1",
        "last_error": None,
        "meta_json": {"synced_by": "import", "note": "initial load"},
    }

    cv, created = upsert_channel_variant(channel_variant_payload)
    print(f"ChannelVariant: {cv}, created={created}")

### set the price for this variant in this channel and price list


    variant_price_payload = {
        "org_code": org_code,
        "price_list_id": pl.pk,
        "channel_variant_id": cv.pk,
        "valid_from": datetime(2025, 1, 1, 0, 0),
        "price": Decimal("19.99"),
        "need_update": False,
    }

    vp, created = upsert_sales_channel_variant_price(variant_price_payload)
    print(f"Price: {vp}, created={created}")

    ############# create test supplier:


    sup_payload = {
        "org_code": org_code,
        "supplier_code": "10001",
        "supplier_description": "Main Widgets Supplier",
        "email": "contact@widgets.example",
        "phone": "+49-123-456789",
        "is_preferred": True,
        "lead_time_days": 14,
    }

    sup, created = upsert_supplier(sup_payload)
    print(f"Supplier: {sup}, created={created}")

    ################################## create supplier product

    #from decimal import Decimal

    sp_payload = {
        "org_code": org_code,
        "supplier_id": sup.pk,
        "variant_id": v.pk,
        "supplier_sku": "SUP-ART-2025",
        "pack_size": Decimal("10.0"),
        "min_order_qty": Decimal("100.0"),
        "lead_time_days": 14,
        "is_active": True,
        "supplier_description": "10mm Steel Bolts",
        "notes": "Special pricing agreed until 2025-12-31",
    }

    sp, created = upsert_supplier_product(sp_payload)
    print(f"SupplierProduct: {sp}, created={created}")
