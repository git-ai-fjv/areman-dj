# apps/imports/services/import_defaults_ops.py
# Created according to the user's permanent Copilot Base Instructions.

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Tuple

from django.db import transaction

from apps.imports.models.import_global_default_set import ImportGlobalDefaultSet
from apps.imports.models.import_global_default_line import ImportGlobalDefaultLine
from apps.imports.models.import_data_type import ImportDataType
from apps.core.models.organization import Organization


@transaction.atomic
def create_default_set(
    org: Organization,
    description: str,
    valid_from: date,
) -> Tuple[ImportGlobalDefaultSet, bool]:
    """
    Get or create an ImportGlobalDefaultSet for the given organization/date.
    Returns (set, created).
    """
    obj, created = ImportGlobalDefaultSet.objects.get_or_create(
        organization=org,
        valid_from=valid_from,
        defaults={"description": description},
    )
    return obj, created


@transaction.atomic
def add_default_line(
    default_set: ImportGlobalDefaultSet,
    target_path: str,
    default_value: Any = None,
    transform: str | None = None,
    is_required: bool = False,
    datatype_code: str = "str",
) -> Tuple[ImportGlobalDefaultLine, bool]:
    """
    Add or update a line in a global default set.

    Args:
        default_set: The parent ImportGlobalDefaultSet
        target_path: e.g. "product.name" or "price.currency_code"
        default_value: Default value to assign
        transform: Optional transform key (e.g. "uppercase")
        is_required: Whether this field is mandatory
        datatype_code: Code in ImportDataType (str, int, decimal, bool, ...)

    Returns:
        (ImportGlobalDefaultLine, created: bool)
    """
    try:
        datatype = ImportDataType.objects.get(code=datatype_code)
    except ImportDataType.DoesNotExist:
        raise RuntimeError(f"Datatype '{datatype_code}' not found in ImportDataType")

    obj, created = ImportGlobalDefaultLine.objects.update_or_create(
        set=default_set,
        target_path=target_path,
        defaults={
            "default_value": default_value,
            "transform": transform,
            "is_required": is_required,
            "target_datatype": datatype,
        },
    )
    return obj, created


@transaction.atomic
def seed_initial_defaults(
    org: Organization,
    valid_from: date
) -> Tuple[ImportGlobalDefaultSet, bool]:
    """
    Create or reuse a default set and fill it with a minimal baseline.
    Returns (default_set, created).
    """

    default_set, created = create_default_set(org, "Initial Global Defaults", valid_from)

    lines: list[Dict[str, Any]] = [
        # ---------------- Product ----------------
        {"target_path": "product.productNumber", "is_required": True, "datatype_code": "str"},
        {"target_path": "product.name", "is_required": True, "datatype_code": "str"},
        {"target_path": "product.org_code", "default_value": org.pk, "is_required": True, "datatype_code": "int"},
        {"target_path": "product.is_active", "default_value": True, "datatype_code": "bool"},

        # ---------------- Variant ----------------
        {"target_path": "variant.origin_code", "default_value": "E", "is_required": True, "datatype_code": "str"},
        {"target_path": "variant.state_code", "default_value": "N", "is_required": True, "datatype_code": "str"},
        {"target_path": "variant.packing_code", "default_value": "1", "is_required": True, "datatype_code": "str"},
        {"target_path": "variant.weight", "default_value": "0.0", "is_required": True, "datatype_code": "decimal"},

        # ---------------- Price ----------------
        {"target_path": "price.currency_code", "default_value": "EUR", "is_required": True, "datatype_code": "str"},
        {"target_path": "price.price", "is_required": True, "datatype_code": "decimal"},

        # ---------------- Supplier ----------------
        {"target_path": "supplier.supplier_code", "is_required": True, "datatype_code": "str"},
        {"target_path": "supplier.is_preferred", "default_value": False, "datatype_code": "bool"},

        # ---------------- Supplier Product ----------------
        {"target_path": "supplier_product.supplier_sku", "is_required": True, "datatype_code": "str"},
        {"target_path": "supplier_product.pack_size", "default_value": 1, "is_required": True, "datatype_code": "decimal"},
        {"target_path": "supplier_product.min_order_qty", "default_value": 1, "is_required": True, "datatype_code": "decimal"},
        {"target_path": "supplier_product.lead_time_days", "default_value": 0, "is_required": True, "datatype_code": "int"},
    ]

    for line in lines:
        add_default_line(
            default_set,
            target_path=line["target_path"],
            default_value=line.get("default_value"),
            transform=line.get("transform"),
            is_required=line.get("is_required", False),
            datatype_code=line.get("datatype_code", "str"),
        )

    return default_set, created
