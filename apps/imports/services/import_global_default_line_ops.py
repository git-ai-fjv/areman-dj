# apps/imports/services/import_global_default_line_ops.py
# Created according to the user's permanent Copilot Base Instructions.

from __future__ import annotations

from typing import Dict, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.imports.models.import_global_default_line import ImportGlobalDefaultLine
from apps.imports.models.import_global_default_set import ImportGlobalDefaultSet


@transaction.atomic
def upsert_import_global_default_line(payload: Dict) -> Tuple[ImportGlobalDefaultLine, bool]:
    """
    Upsert an ImportGlobalDefaultLine via dict.

    Required: set_id, target_path
    Optional: default_value, transform, is_required

    Returns: (line_obj, created)
    Raises: ValidationError, IntegrityError
    """
    required = ["set_id", "target_path"]
    missing = [k for k in required if payload.get(k) in (None, "")]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    try:
        set_obj = ImportGlobalDefaultSet.objects.get(id=payload["set_id"])
    except ImportGlobalDefaultSet.DoesNotExist:
        raise ValidationError(f"ImportGlobalDefaultSet with id {payload['set_id']} not found")

    defaults = {
        "default_value": payload.get("default_value"),
        "transform": payload.get("transform"),
        "is_required": bool(payload.get("is_required", False)),
    }

    obj, created = ImportGlobalDefaultLine.objects.update_or_create(
        set=set_obj,
        target_path=payload["target_path"],
        defaults=defaults,
    )
    return obj, created


#
# from apps.imports.services.import_global_default_line_ops import upsert_import_global_default_line
#
# line, created = upsert_import_global_default_line({
#     "set_id": 1,
#     "target_path": "product.is_active",
#     "default_value": True,
#     "transform": "bool",
#     "is_required": True,
# })
# print(line.id, created)


