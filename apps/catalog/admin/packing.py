# apps/catalog/admin/packing.py
#!/usr/bin/env python3
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations

from django.contrib import admin

from ..models.packing import Packing


@admin.register(Packing)
class PackingAdmin(admin.ModelAdmin):
    """Admin for Packing.

    We avoid guessing field names by showing a generic label that uses __str__.
    This keeps list rows clickable (standing rule) without assuming model fields.
    """

    # Keep rows clickable/editable without assuming concrete field names.
    list_display = ("object_label",)
    list_display_links = ("object_label",)

    # Keep the list snappy.
    list_per_page = 50

    def object_label(self, obj) -> str:
        """Return a human-readable label for the list view."""
        return str(obj)

    object_label.short_description = "Packing"
