# apps/imports/services/transform_utils.py
# Created according to the user's permanent Copilot Base Instructions.

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from apps.imports.models.import_transform_type import ImportTransformType


def apply_transform(value: Any, transform: Optional[ImportTransformType]) -> Any:
    """
    Apply a transformation to a value based on ImportTransformType.

    Args:
        value: Input value (string, int, etc.)
        transform: ImportTransformType instance or None

    Returns:
        Transformed value
    """
    if transform is None:
        return value

    code = transform.code

    try:
        if code == "uppercase":
            return str(value).upper() if value is not None else None
        elif code == "lowercase":
            return str(value).lower() if value is not None else None
        elif code == "strip":
            return str(value).strip() if value is not None else None
        elif code == "int":
            return int(value) if value not in (None, "") else None
        elif code == "decimal":
            return Decimal(str(value)) if value not in (None, "") else None
        elif code == "bool":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.strip().lower() in ("1", "true", "yes", "y")
            return bool(value)
        else:
            # Unknown transform → return unchanged
            return value
    except (ValueError, InvalidOperation):
        # If conversion fails, return None for safety
        return None


