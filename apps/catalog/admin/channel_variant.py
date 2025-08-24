# apps/catalog/admin.py
# Created according to the user's Copilot Base Instructions.
from __future__ import annotations
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from apps.catalog.models.channel_variant import ChannelVariant


class ChannelVariantAdmin(admin.ModelAdmin):
    """Admin for ChannelVariant."""
    list_display = (
        "id",
        "organization_id",   # org_code
        "channel",           # FK display
        "variant",           # FK display
        "publish",
        "is_active",
        "need_shop_update",
        "shop_product_id",
        "shop_variant_id",
        "last_synced_at",
        "updated_at",
    )
    list_display_links = ("id", "variant")  # rows clickable
    search_fields = (
        "channel__channel_code",
        "channel__channel_name",
        "shop_item_id",
        "shop_variant_id",
    )
    list_filter = ("publish", "is_active", "need_shop_update")
    list_select_related = ("organization", "channel", "variant")
    ordering = ("organization_id", "channel_id", "variant_id")


# Idempotent registration to avoid crashes on double import/autoreload
try:
    admin.site.register(ChannelVariant, ChannelVariantAdmin)
except AlreadyRegistered:
    pass

