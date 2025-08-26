# apps/imports/services/import_global_default_set_ops.py
# Created according to the user's permanent Copilot Base Instructions.

from __future__ import annotations

from typing import Dict, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.core.models.organization import Organization
from apps.imports.models.import_global_default_set import ImportGlobalDefaultSet


@transaction.atomic
def upsert_import_global_default_set(payload: Dict) -> Tuple[ImportGlobalDefaultSet, bool]:
    """
    Upsert an ImportGlobalDefaultSet via dict.

    Required: org_code, description, valid_from
    Optional: none

    Returns: (set_obj, created)
    Raises: ValidationError, DoesNotExist, IntegrityError
    """
    required = ["org_code", "description", "valid_from"]
    missing = [k for k in required if payload.get(k) in (None, "")]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    try:
        org = Organization.objects.get(org_code=payload["org_code"])
    except Organization.DoesNotExist:
        raise ValidationError(f"Organization with org_code {payload['org_code']} not found")

    defaults = {}
    obj, created = ImportGlobalDefaultSet.objects.update_or_create(
        organization=org,
        description=payload["description"],
        valid_from=payload["valid_from"],
        defaults=defaults,
    )
    return obj, created


#
# from apps.imports.services.import_global_default_set_ops import upsert_import_global_default_set
#
# s, created = upsert_import_global_default_set({
#     "org_code": 1,
#     "description": "Global Defaults 2025",
#     "valid_from": "2025-01-01",
# })
# print(s.id, created)
