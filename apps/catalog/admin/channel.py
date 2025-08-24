# Created according to the user's permanent Copilot Base Instructions.
from __future__ import annotations
from django.contrib import admin
from apps.catalog.models.channel import Channel


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    """Admin for Channel."""
    # Keep it simple and useful in lists:
    list_display = (
        "id",
        "organization_id",  # org_code (FK to Organization)
        "channel_code",
        "channel_name",
        "kind",
        "base_currency",    # FK display (Currency)
        "is_active",
        "updated_at",
    )
    # Rows clickable (required by your standing rule)
    list_display_links = ("id", "channel_code")

    # Helpful search on codes/names and related keys
    search_fields = (
        "channel_code",
        "channel_name",
        "organization__org_code",
        "base_currency__code",
    )

    # Quick filters
    list_filter = ("is_active", "kind", "base_currency")

    # Minor QoL for performance
    list_select_related = ("organization", "base_currency")
    ordering = ("organization_id", "channel_code")
