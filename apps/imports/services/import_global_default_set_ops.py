# apps/imports/services/import_global_default_set_ops.py
# Created according to the user's permanent Copilot Base Instructions.

from __future__ import annotations

from typing import Dict, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.imports.models.import_global_default_set import ImportGlobalDefaultSet


@transaction.atomic
def upsert_import_global_default_set(payload: Dict) -> Tuple[ImportGlobalDefaultSet, bool]:
    """
    Upsert an ImportGlobalDefaultSet via dict.

    Required: description, valid_from
    Optional: none

    Returns: (set_obj, created)
    Raises: ValidationError, IntegrityError
    """
    required = ["description", "valid_from"]
    missing = [k for k in required if payload.get(k) in (None, "")]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    defaults = {}
    obj, created = ImportGlobalDefaultSet.objects.update_or_create(
        description=payload["description"],
        valid_from=payload["valid_from"],
        defaults=defaults,
    )
    return obj, created


#
# from apps.imports.services.import_global_default_set_ops import upsert_import_global_default_set
#
# s, created = upsert_import_global_default_set({
#     "description": "Global Defaults 2025",
#     "valid_from": "2025-01-01",
# })
# print(s.id, created)


