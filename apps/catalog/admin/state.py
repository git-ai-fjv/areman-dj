# apps/catalog/admin/state.py
#!/usr/bin/env python3
# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations

from django.contrib import admin

from ..models.state import State


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    """Admin for State master data."""

    # Show key fields and make rows clickable (standing rule).
    list_display = ("state_code", "state_description")
    list_display_links = ("state_code", "state_description")

    # Useful search and stable ordering.
    search_fields = ("state_code", "state_description")
    ordering = ("state_code",)

    # Keep the changelist snappy.
    list_per_page = 50


