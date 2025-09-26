# apps/imports/services/defaults.py
"""
Purpose:
    Provides utilities for retrieving and assembling active global default sets
    into structured dictionaries for use during import processing.

Context:
    Part of the `apps.imports.services` package.
    Used to look up ImportGlobalDefaultSet entries and group their lines
    (e.g., product, variant, price, supplier, supplier_product) into nested dicts.

Used by:
    - Import pipelines and services that need a ready-to-use defaults dictionary
    - Local testing (via __main__ execution)

Depends on:
    - apps.imports.models.import_global_default_set.ImportGlobalDefaultSet
    - Django ORM for querying active default sets
    - django.utils.timezone for date comparison

Example:
    from apps.imports.services.defaults import build_base_dict

    base_dict = build_base_dict(org_id=1)
    print(base_dict["product"]["name"])
"""


from __future__ import annotations

from typing import Any, Dict

import scripts.bootstrap_django  # noqa: F401

from django.utils import timezone
from apps.imports.models.import_global_default_set import ImportGlobalDefaultSet


def get_active_default_set(org_id: int) -> ImportGlobalDefaultSet:
    """
    Return the active ImportGlobalDefaultSet for an organization, based on valid_from.
    """
    return (
        ImportGlobalDefaultSet.objects.filter(organization_id=org_id, valid_from__lte=timezone.now())
        .order_by("-valid_from")
        .first()
    )


def build_base_dict(org_id: int) -> Dict[str, Dict[str, Any]]:
    """
    Build a base dict structure with global defaults, grouped into subdicts.

    Returns a dictionary with predefined subdicts, e.g.:
    {
        "product": {...},
        "variant": {...},
        "price": {...},
        "supplier": {...},
        "supplier_product": {...}
    }
    """

    default_set = get_active_default_set(org_id)
    if not default_set:
        raise RuntimeError(f"No ImportGlobalDefaultSet found for org_id={org_id}")

    base: Dict[str, Dict[str, Any]] = {
        "product": {},
        "variant": {},
        "price": {},
        "supplier": {},
        "supplier_product": {},
    }

    for line in default_set.global_default_lines.all():
        # Expect target_path like "product.name" or "variant.state_code"
        if "." not in line.target_path:
            section, key = "product", line.target_path
        else:
            section, key = line.target_path.split(".", 1)

        if section not in base:
            base[section] = {}

        base[section][key] = line.default_value

    return base


# ---------------------------------------------------------------------------
# Local test runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import django
    import os
    #import pprint
    import scripts.bootstrap_django  # noqa: F401
    import pprint

    # 🔌 Bootstrap Django environment
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lnd_manage.settings")
    django.setup()

    ORG_ID = 1

    try:
        base_dict = build_base_dict(ORG_ID)
        print("✅ Built base dict:")
        pprint.pp(base_dict)
    except Exception as e:
        print(f"❌ Error: {e}")

