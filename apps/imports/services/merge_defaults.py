#!/usr/bin/env python3

# apps/imports/services/merge_defaults.py
"""
Purpose:
    Utility functions to merge global defaults into normalized records.

    - load_defaults(org): load defaults as dict
    - merge_defaults(data, org): merge dict with defaults (defaults first)

Example:
    from apps.imports.services import merge_defaults

    defaults = merge_defaults.load_defaults(org)
    merged = merge_defaults.merge_defaults(mapped, org)
"""

from __future__ import annotations
from typing import Any, Dict
from datetime import date

from apps.imports.models.import_global_default_set import ImportGlobalDefaultSet
from apps.imports.models.import_global_default_line import ImportGlobalDefaultLine


def load_defaults(org) -> Dict[str, Any]:
    """
    Load the newest ImportGlobalDefaultSet for an organization and return as dict.

    Args:
        org: Organization instance

    Returns:
        dict of {target_path: default_value}
    """
    default_set = (
        ImportGlobalDefaultSet.objects.filter(organization=org, valid_from__lte=date.today())
        .order_by("-valid_from")
        .first()
    )
    if not default_set:
        return {}

    lines = ImportGlobalDefaultLine.objects.filter(set=default_set)
    return {line.target_path: line.default_value for line in lines}


def merge_defaults(data: Dict[str, Any], org) -> Dict[str, Any]:
    """
    Merge global defaults into given dict (defaults first, data overwrites).

    Args:
        data: already mapped supplier dict
        org: Organization instance

    Returns:
        dict with defaults merged in
    """
    merged = load_defaults(org)
    merged.update(data)
    return merged
