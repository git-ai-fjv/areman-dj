#!/usr/bin/env python3
# scripts/debug_import_global_defaults.py
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations

from datetime import date

# 🔌 Bootstrap Django environment
import scripts.bootstrap_django  # noqa: F401

from apps.core.models.organization import Organization
from apps.imports.models.import_global_default_set import ImportGlobalDefaultSet
from apps.imports.models.import_global_default_line import ImportGlobalDefaultLine


org_code = 1  # Default org for testing

if __name__ == "__main__":
    # Load organization
    org = Organization.objects.get(org_code=org_code)

    # Create a new Default Set
    set_obj, created = ImportGlobalDefaultSet.objects.get_or_create(
        organization=org,
        description="Global Defaults 2025",
        valid_from=date(2025, 1, 1),
    )
    print(f"DefaultSet: {set_obj}, created={created}")

    # Create Default Lines for this Set
    lines = [
        {
            "target_path": "product.is_active",
            "default_value": True,
            "transform": "bool",
            "is_required": True,
        },
        {
            "target_path": "variant.origin_code",
            "default_value": "E",
            "transform": "str",
            "is_required": True,
        },
        {
            "target_path": "price_list.kind",
            "default_value": "S",
            "transform": "str",
            "is_required": True,
        },
        {
            "target_path": "channel.channel_code",
            "default_value": "WEB",
            "transform": "str",
            "is_required": True,
        },
        {
            "target_path": "channel.base_currency_code",
            "default_value": "EUR",
            "transform": "str",
            "is_required": True,
        },
    ]

    for line in lines:
        obj, created = ImportGlobalDefaultLine.objects.update_or_create(
            set=set_obj,
            target_path=line["target_path"],
            defaults={
                "default_value": line["default_value"],
                "transform": line["transform"],
                "is_required": line["is_required"],
            },
        )
        print(f"Line: {obj}, created={created}")

