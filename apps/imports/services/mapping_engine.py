#!/usr/bin/env python3
# apps/imports/services/mapping_engine.py

"""
Purpose:
    Apply an ImportMapSet to raw supplier payloads and produce normalized dicts.
    Used by normalize_records and other import processing commands.

Example:
    from apps.imports.services.mapping_engine import apply_mapping
    normalized = apply_mapping(payload, map_set)
    print(normalized)
"""

from __future__ import annotations
from typing import Any, Dict
import decimal

from apps.imports.models.import_map_set import ImportMapSet
from apps.imports.models.import_map_detail import ImportMapDetail
from apps.imports.services.transform_utils import apply_transform


def make_json_safe(data: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively convert values so they can be JSON serialized.
    - Decimal -> float
    - Sets -> Lists
    - Other unknown types -> str
    """
    def convert(val):
        if isinstance(val, decimal.Decimal):
            return float(val)
        if isinstance(val, set):
            return list(val)
        if isinstance(val, dict):
            return {k: convert(v) for k, v in val.items()}
        if isinstance(val, list):
            return [convert(v) for v in val]
        return val

    return {k: convert(v) for k, v in data.items()}


def apply_mapping(payload: dict[str, Any], map_set: ImportMapSet) -> dict[str, Any]:
    """
    Transform a raw payload dict into normalized structure using map_set.

    Args:
        payload: The raw supplier payload (dict).
        map_set: ImportMapSet instance with related ImportMapDetails.

    Returns:
        Normalized dict with mapped + transformed values (JSON-safe).
    """
    normalized: Dict[str, Any] = {}

    for detail in map_set.map_details.select_related("target_datatype").all():
        raw_value = payload.get(detail.source_path)
        value = raw_value

        # optional transform
        if detail.transform:
            # treat transform as ImportTransformType code
            value = apply_transform(
                raw_value, type("Tmp", (), {"code": detail.transform})()
            )

        # enforce datatype
        dt_code = detail.target_datatype.code
        try:
            if dt_code == "int" and value not in (None, ""):
                value = int(value)
            elif dt_code == "decimal" and value not in (None, ""):
                value = decimal.Decimal(str(value))
            elif dt_code == "bool":
                if isinstance(value, str):
                    value = value.strip().lower() in ("1", "true", "yes", "y")
                else:
                    value = bool(value) if value not in (None, "") else None
            elif dt_code == "str" and value is not None:
                value = str(value)
        except Exception:
            value = None

        normalized[detail.target_path] = value

    # ensure JSONField compatibility
    return make_json_safe(normalized)
