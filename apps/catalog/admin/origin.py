# apps/catalog/admin/origin.py
#!/usr/bin/env python3
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations

from django.contrib import admin

from ..models.origin import Origin


@admin.register(Origin)
class OriginAdmin(admin.ModelAdmin):
    """Admin for Origin master data."""

    # Show key fields and make the row clickable (standing rule).
    list_display = ("origin_code", "origin_description")
    list_display_links = ("origin_code", "origin_description")

    # Useful search and stable ordering.
    search_fields = ("origin_code", "origin_description")
    ordering = ("origin_code",)

    # Keep the list snappy.
    list_per_page = 50
